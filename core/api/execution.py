#coding:utf8
import re
import uuid
import time
import redis
import json
import base64
from rest_framework.response import Response

from libs import baseview, util, redis_pool
from libs.util import error_capture,HashCURD
from conf import config

redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()


class mysession(baseview.BaseView):
    '''
    获取playbook的session参数
    '''
    @error_capture 
    def get(self, request, args = None):
        pre_job_name = request.GET['filter']
        
        tmpl_key = redis_manage_client.hget(pre_job_name,config.prefix_exec_tmpl)
        playbook = redis_manage_client.hget(tmpl_key,'playbook')

        session_vars=[]
        with open(playbook,'r') as f:   
            l=f.readline()
            #存在bug 注释被获取,如            echo xxx # {{session.YYYY}}
            #但不应排除#只后的字符串 如   echo "#" {{session.YYYY}}
            while l:
                if not re.match('^#',l):
                    session_vars=session_vars+re.findall('(?<={{'+config.playbook_prefix_session+'\.).*?(?=}})',l)
                l=f.readline()     
        
        session_vars = list(set(session_vars))
        #print session_vars
        
        session_tag = config.prefix_session
        session_info = {}
        old_session_info = redis_config_client.hgetall(session_tag+pre_job_name)
        for v in session_vars:
            session_info[v] = old_session_info.get(v,'')            

        return Response({'status':1,'vars':session_info})

   
class myexecution(baseview.BaseView): 
    '''
    执行任务
    '''
    @error_capture
    def post(self, request, args = None):

        filter = request.GET['filter']
        #jwt_str_raw=request.META['HTTP_AUTHORIZATION']  #需要在header的字段前加http_ 同时必须为大写
        #jwt_str =jwt_str_raw.split('.')[1]+"=="     
        #user=json.loads(base64.b64decode(jwt_str))['username']
        #print user 
        user=str(request.user)
        job_id=uuid.uuid1().hex
        data = request.data
        session_tag = config.prefix_session
        if data:
            redis_config_client.hmset(session_tag+filter,data)
            redis_config_client.hmset(session_tag+filter+'_'+job_id,data)
            redis_config_client.expire(session_tag+filter+'_'+job_id,24*60*60)

        job_info = redis_manage_client.hgetall(filter)
        
        tmpl_key = redis_manage_client.hget(filter,config.prefix_exec_tmpl)
        
        if tmpl_key:
            tmpl_info=redis_manage_client.hgetall(tmpl_key)
            for k in tmpl_info.keys():
                if k not in job_info.keys():
                    job_info[k]=tmpl_info[k]

        job_name = config.prefix_job+job_id
        job_info['session'] = session_tag+filter+'_'+job_id
        job_info['begin_time'] = time.time()        
        job_info['user'] = user   

        redis_job_client.hmset(job_name,job_info)        

        redis_send_client.rpush(config.key_job_list,job_name)  

        return Response({'status':1,'data':job_name}) 

        
    @error_capture
    def get(self, request, args = None):

        old_job_id = request.GET['work_id']
        cluster_str = request.GET['cluster_str']  

        job_info = redis_job_client.hgetall(old_job_id)
        job_id = uuid.uuid1().hex

        old_session_name=job_info[config.playbook_prefix_session]
        new_session_name=old_session_name+'_'+job_id
        job_info[config.playbook_prefix_session]=new_session_name

        session_data=redis_config_client.hgetall(old_session_name)
        if session_data:
            redis_config_client.hmset(new_session_name,session_data)
            redis_config_client.expire(new_session_name,config.session_var_expire_sec)

        if args == 'rerun':
            cluster_id = request.GET['cluster_id']
            begin_host = request.GET.get('begin_host','')
            begin_line = int(request.GET.get('begin_line',0))
 
            new_cluster_id = uuid.uuid1().hex
            
            redis_config_client.hmset(cluster_str+'_'+new_cluster_id,redis_config_client.hgetall(cluster_str+'_'+cluster_id))
            global_data=redis_config_client.hgetall(config.prefix_global+cluster_id)
            if global_data:
                redis_config_client.hmset(config.prefix_global+new_cluster_id,global_data)
                #在此提前设置过期时间 防止执行到一半失败是global_xxx一直存在 命令分发后端会在执行结束后再设置一次
                redis_config_client.expire(config.prefix_global+new_cluster_id,config.global_var_expire_sec)

            job_name = config.prefix_job+job_id
                        
            job_info['cluster_str'] = cluster_str+config.cmd_spliter+new_cluster_id
            job_info['begin_time'] = time.time() 
            job_info['job_type'] = 'rerun'
            job_info['_number'] = len(cluster_str.split(','))
            if begin_host:
                job_info['begin_host'] = begin_host
            if begin_line:
                job_info['begin_line'] = begin_line
            
            redis_job_client.hmset(job_name,job_info)
            
            rerun_str=''
            if redis_log_client.hget(config.prefix_log+old_job_id,'rerun'):
                rerun_str=redis_log_client.hget(config.prefix_log+old_job_id,'rerun')+','+job_name
            else:
                rerun_str=job_name

            redis_log_client.hset(config.prefix_log+old_job_id,'rerun',rerun_str)
            
            redis_send_client.rpush(config.key_job_list,job_name) 

            return Response({'status':1,'data':job_name})

            
        elif args == 'rerun_info':
            cluster_id = request.GET.get('cluster_id','')  

            rerun_info={}
            _rerun_info=redis_config_client.hgetall(job_info.get(config.playbook_prefix_session,''))  
            rerun_info[config.playbook_prefix_session]=_rerun_info
            
            readonly={}
            readonly['playbook']=job_info['playbook']
            readonly['cluster_str']=cluster_str            
            rerun_info['readonly']=readonly

            changable={}
            _len=int(redis_log_client.llen(config.prefix_log_cluster+cluster_id))
            changable['begin_line']=_len
            
            begin_host=''
            if cluster_id:
                begin_host=redis_log_client.hget(redis_log_client.lrange(config.prefix_log_cluster+cluster_id,_len-1,_len)[0],'exe_host') 
            changable['begin_host']=begin_host

            rerun_info['changable']=changable

            return Response({'status':1,'data':rerun_info}) 
            
            
class executioninfo(baseview.BaseView): 
    '''
    任务、任务模板的增删改查 
    '''    
    @error_capture
    def get(self, request, args = None):
        return HashCURD.get(redis_manage_client,request, args)

    @error_capture
    def post(self, request, args = None):
        return HashCURD.post(redis_manage_client,request, args)


