#coding:utf8
import os
import re
import sys
import uuid
import time
import yaml
import redis
import json
import base64

from jinja2 import Template
from rest_framework.response import Response
from django.conf import settings

from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import HashCURD,playbook_root,playbook_temp
from libs.redis_pool import redis_single


def get_session(pre_job_name,redis_manage_client,redis_config_client):
    tmpl_key = redis_manage_client.hget(pre_job_name,config.prefix_exec_tmpl)
    playbook = redis_manage_client.hget(tmpl_key,'playbook')
    session_vars=[]
    playbook = os.path.join(playbook_root,playbook)
    with open(playbook,'r') as f:   
        l=f.readline()
        #存在bug 注释被获取,如            echo xxx # {{session.YYYY}}
        #但不应排除#只后的字符串 如   echo '#' {{session.YYYY}}
        while l:
            if not re.match('^#',l):
                session_vars=session_vars+re.findall('(?<={{'+config.prefix_session+'\.).*?(?=}})',l)
            l=f.readline()     
    
    session_vars = list(set(session_vars))
    
    session_tag = config.prefix_session
    session_info = {}
    old_session_info = redis_config_client.hgetall(session_tag+config.spliter+pre_job_name)

    for v in session_vars:
        session_info[v] = old_session_info.get(v,'')

    return session_info


class Session(baseview.BaseView):

    def get(self, request, args = None):
        redis_config_client = redis_single['redis_config']
        redis_manage_client = redis_single['redis_manage']

        pre_job_name = request.GET['filter']
        
        if not args:
            '''
            获取playbook的session参数
            '''
            session_info = get_session(pre_job_name,redis_manage_client,redis_config_client) 

            return Response({'status':1,'vars':session_info})

        if args == 'extend':
            '''
            获取更完善的session
            '''
            tmpl_key = redis_manage_client.hget(pre_job_name,config.prefix_exec_tmpl)
            playbook = redis_manage_client.hget(tmpl_key,'playbook')
            playbook = os.path.join(playbook_root,playbook)
            playbook_str =  open(playbook).read()

            #在playbook头部以注释引入session说明时格式如下
            """
            #CONTENT-BEGIN
            #yaml_str
            #CONTENT-END
            """
            yaml_str_raw=re.findall('#CONTENT-BEGIN([\\w|\\W]*?)#CONTENT-END',playbook_str)
            if yaml_str_raw:
                yaml_str=yaml_str_raw[0].replace('\n#','\n')
            else:
                try:
                    #或者通过单独的yaml文件说明session格式
                    yaml_str =  open(playbook+'.conf').read()
                except:
                    yaml_str =  ""

            if sys.version_info>(3,0):
                from io import StringIO
                f=StringIO(yaml_str)
                yaml_dict=yaml.load(f,Loader=yaml.FullLoader)
            else:
                from StringIO import StringIO
                f=StringIO(yaml_str)
                yaml_dict=yaml.load(f)            

            if not yaml_dict:
                yaml_dict = {}

            var=get_session(pre_job_name,redis_manage_client,redis_config_client)

            sesion_list=[]
            if 'session' in yaml_dict:
                for k1 in yaml_dict['session']:
                    for k2 in var.keys():
                        if k1['key']==k2:
                            k1['value']=var[k2]
                    if 'value' in k1:
                        sesion_list.append(k1)
                
                key_constrict=[]
                for k1 in yaml_dict['session']:
                    key_constrict.append(k1['key'])
                
                for k2 in var.keys():
                    if not k2 in key_constrict:
                        sesion_list.append({'key':k2,'value':var[k2]})
            else:
                for k2 in var.keys():
                    sesion_list.append({'key':k2,'value':var[k2]})

            return Response({'status':1,'session':sesion_list})


    def post(self, request, args = None):
        '''
        提交session参数
        '''
        if not args:
            redis_config_client = redis_single['redis_config']
    
            filter = request.GET['filter']
            data = request.data
    
            session_tag = config.prefix_session
            if data:
                data=util.plain_dict(data)
    
                redis_config_client.hmset(session_tag+config.spliter+filter,data)
    
            return Response({'status':1,'vars':data})

        elif args == 'temp':
            #提交临时session
            data = request.data
            if not data:
                return Response({'status':-1,'msg':util.safe_decode('空数据不必提交')})

            redis_tmp_client = redis_single['redis_tmp']
            
            job_id=uuid.uuid1().hex
            session_name=config.prefix_session+config.spliter+job_id
            redis_tmp_client.hmset(session_name,data)

            return Response({'status':1,'job_id':job_id,'session':session_name})

        #return Response({'status':-1,'msg':"error args","args":args})


class Execution(baseview.BaseView): 
    '''
    执行任务
    '''
    def post(self, request, args = None):
        '''
        执行任务
        '''
        redis_send_client = redis_single['redis_send']
        redis_tmp_client = redis_single['redis_tmp']
        redis_config_client = redis_single['redis_config']
        redis_job_client = redis_single['redis_job']
        redis_manage_client = redis_single['redis_manage']

        exec_name = request.GET['filter']
        #jwt_str_raw=request.META['HTTP_AUTHORIZATION']  #需要在header的字段前加http_ 同时必须为大写
        #jwt_str =jwt_str_raw.split('.')[1]+'=='     
        #user=json.loads(base64.b64decode(jwt_str))['username']
        #print(user) 
        user=str(request.user)
        data = request.data

        job_id=uuid.uuid1().hex
        #session_tag = config.prefix_session
        session_tag = config.prefix_session
        if data:
            data=util.plain_dict(data)
            redis_config_client.hmset(session_tag+config.spliter+exec_name,data)
            redis_tmp_client.hmset(session_tag+config.spliter+job_id,data)
            redis_tmp_client.expire(session_tag+config.spliter+job_id,24*60*60)

        job_info = redis_manage_client.hgetall(exec_name)
        
        tmpl_key = redis_manage_client.hget(exec_name,config.prefix_exec_tmpl)
        
        if tmpl_key:
            tmpl_info=redis_manage_client.hgetall(tmpl_key)
            for k in tmpl_info.keys():
                if k not in job_info.keys():
                    job_info[k]=tmpl_info[k]

        job_name = config.prefix_job+job_id
        job_info['session'] = session_tag+config.spliter+job_id
        job_info['begin_time'] = time.time()        
        job_info['user'] = user   

        redis_job_client.hmset(job_name,job_info)        

        redis_send_client.rpush(config.key_job_list,job_name)  

        return Response({'status':1,'data':job_name}) 

        
    def get(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        redis_log_client = redis_single['redis_log']
        redis_tmp_client = redis_single['redis_tmp']
        redis_job_client = redis_single['redis_job']

        old_job_id = request.GET['work_id']
        target = request.GET['target']  
        target_id = request.GET['target_id']

        job_info = redis_job_client.hgetall(old_job_id)

        if args == 'rerun':
            '''
            重新执行单个执行
            ''' 
            
            begin_line = int(request.GET.get('begin_line',0))            

            _job_id = request.GET.get('new_job_id','')
            if _job_id:
                job_id = _job_id
            else:
                job_id = uuid.uuid1().hex
            job_name = config.prefix_job+job_id

            new_session_name=config.prefix_session+config.spliter+job_id
            if _job_id:
                #如果传入带有new_job_id，说明已经设置好session，不需要再设置
                job_info[config.prefix_session]=new_session_name
            else:
                try:
                    session_data=redis_tmp_client.hgetall(redis_tmp_client.hget(target+config.spliter+target_id,config.prefix_session))
                except:
                    session_data={}

                #有些任务可能不存在session
                if session_data:
                    redis_tmp_client.hmset(new_session_name,session_data)
                    redis_tmp_client.expire(new_session_name,config.tmp_config_expire_sec)
                    job_info[config.prefix_session]=new_session_name

            new_target_id = uuid.uuid1().hex
            
            redis_tmp_client.hmset(target+config.spliter+new_target_id,redis_tmp_client.hgetall(target+config.spliter+target_id))
            global_data=redis_tmp_client.hgetall(config.prefix_global+config.spliter+target_id)
            if global_data:
                redis_tmp_client.hmset(config.prefix_global+config.spliter+new_target_id,global_data)
                #在此提前设置过期时间 防止执行到一半失败时global_xxx一直存在 命令分发后端会在执行结束后再设置一次
                redis_tmp_client.expire(config.prefix_global+config.spliter+new_target_id,config.tmp_config_expire_sec)

            job_info['target'] = target+config.spliter+new_target_id
            job_info['begin_time'] = time.time() 
            job_info['job_type'] = config.job_rerun
            job_info['number'] = len(target.split(','))
            
            if begin_line:
                job_info['begin_line'] = begin_line
            
            redis_job_client.hmset(job_name,job_info)
            
            rerun_str=''
            if redis_log_client.hget(config.prefix_log+old_job_id, config.job_rerun):
                rerun_str=redis_log_client.hget(config.prefix_log+old_job_id,config.job_rerun)+','+job_name
            else:
                rerun_str=job_name

            redis_log_client.hset(config.prefix_log+old_job_id,config.job_rerun,rerun_str)
            
            redis_send_client.rpush(config.key_job_list,job_name) 

            return Response({'status':1,'data':job_name})

            
        elif args == 'rerun_info':
            '''
            单个执行的重新执行信息
            '''
            #target_id = request.GET.get('target_id','')  

            rerun_info={}
            try:
                session_data=redis_tmp_client.hgetall(redis_tmp_client.hget(target+config.spliter+target_id,config.prefix_session))
            except:
                session_data={}

            rerun_info[config.prefix_session]=session_data
            
            readonly={}
            readonly['playbook']=job_info['playbook']
            readonly['target']=target            
            rerun_info['readonly']=readonly

            changable={}
            _len=int(redis_log_client.llen(config.prefix_log_target+target_id))
            changable['begin_line']=_len
            
            rerun_info['changable']=changable

            return Response({'status':1,'data':rerun_info}) 
            
            
class ExecutionInfo(baseview.BaseView): 
    '''
    任务、任务模板的增删改查 
    '''    
    def get(self, request, args = None):
        redis_manage_client = redis_single['redis_manage']
        return HashCURD.get(redis_manage_client,request, args)

    def post(self, request, args = None):
        redis_manage_client = redis_single['redis_manage']
        return HashCURD.post(redis_manage_client,request, args)


class FastExecution(baseview.BaseView): 
    '''
    快速任务
    快速任务直接由提交的信息执行，不再依赖存储的对象信息以及存储的 playbook
    '''
    def post(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        redis_tmp_client = redis_single['redis_tmp']
        redis_job_client = redis_single['redis_job']

        user=str(request.user)
        data = request.data
        try:
            spliter = data['spliter']
            parallel = data['parallel']
            exeinfo = data['exeinfo']
            playbook = data['playbook']
        except:
            return Response({'status':-1,'msg': util.safe_decode('提交的数据必须包含以下属性： spliter、parallel、exeinfo、playbook'),'data':data}) 
        
        target_info=[]
        #使用配置信息构造playbook
        playbook_all=''
        try:
            i = 0
            #for t in target_info:
            for l in exeinfo.split('\n'):
                i = i+1
                if (re.match("^#",l.strip())) or (not l.strip()):
                    #跳过 注释开头的行以及空行
                    target_info.append({})
                    continue

                j=1
                t = {}
                # _1 _2 _3 ... 对应一行分割后的字符 __ 对应一行
                for x in l.split(spliter):
                    t['_'+str(j)] = x.strip()
                    j = j+1

                t['__'] = l    
                target_info.append(t)

                playbook_new=playbook
                for c in re.findall('(?<={{).+?(?=}})',playbook):
                    # 只对 _1 _2 _3 ... __ 判断值是否存在
                    if re.match('(^(_\\d+)$)|(^__$)', c.strip()): 
                        if c.strip() in t:
                            playbook_new=re.sub('{{'+c+'}}',t[c.strip()],playbook_new)
                            print(playbook_new)
                        else:
                            raise Exception('render error')

                playbook_all = playbook_all + playbook_new + '\n'
                #存在错误，使用global参数时由于没有值，出现渲染失败
                #playbook_all = playbook_all + Template(playbook).render(t) + '\n'
                
        except:
            from traceback import format_exc
            print(format_exc())
            return Response({'status':-2,'msg': util.safe_decode('第 %d 行配置信息错误！ \n%s' %(i, str(t)))}) 

        playbook_file = os.path.join(playbook_temp, config.prefix_temp + uuid.uuid1().hex)
        _path=os.path.dirname(playbook_file)
        if not os.path.exists(_path):
            os.makedirs(_path)

        def get_target_name(n=0):
            #t = config.prefix_temp + uuid.uuid1().hex + config.spliter + uuid.uuid1().hex
            t = config.prefix_temp + str(n) + config.spliter + uuid.uuid1().hex
            return t

        job_info = {}

        if (isinstance(parallel,str) and parallel == 'true') or \
            (isinstance(parallel,int) and parallel > 0) or (isinstance(parallel,int) and parallel):
            #并行执行

            target_list=[]
            i=0
            for t in target_info:
                i=i+1
                if t:
                    target_name=get_target_name(i)
                    redis_tmp_client.hmset(target_name,t)
                    redis_tmp_client.expire(target_name,config.tmp_config_expire_sec)
                    target_list.append(target_name)

            with open(playbook_file,'w') as f:
                if playbook[-1] != '\n':
                    playbook = playbook + '\n'
                
                try:
                    f.write(playbook)
                except:
                    #python2需要由unicode转码之后才能输出
                    f.write(playbook.encode('utf8'))

            job_info['target'] = ','.join(target_list)
            job_info['number'] = len(target_list)
            job_info['comment'] = '快速任务-并行'  
            
        else:
            #串行执行
            #设置一个临时对象 里面的信息不会被使用
            target_name=get_target_name()
            redis_tmp_client.hmset(target_name,{'t':time.time()})
            redis_tmp_client.expire(target_name,config.tmp_config_expire_sec)

            with open(playbook_file,'w') as f:
                try:
                    f.write(playbook_all)
                except:
                    f.write(playbook_all.encode('utf8'))

            job_info['target'] = target_name
            job_info['number'] = 1
            job_info['comment'] = '快速任务-串行'  


        job_info['playbook'] = playbook_file
        job_info['user'] = user
        job_info['begin_time'] = time.time()
        job_info['target_type'] ='temp'
        job_info['job_type'] ='temp'


        job_id = uuid.uuid1().hex
        job_name = config.prefix_job+job_id

        redis_job_client.hmset(job_name,job_info)        
        redis_send_client.rpush(config.key_job_list,job_name)  

        return Response({'status':1,'data':job_name}) 

