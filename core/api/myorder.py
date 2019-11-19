#coding:utf8
import time
import redis
from rest_framework.response import Response

from libs import baseview, util, redis_pool
from libs.util import error_capture,safe_decode
from conf import config

redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()

class myorder(baseview.BaseView):
    '''
    获取工单列表

    '''
    @error_capture    
    def get(self, request, args = None):
        page = request.GET.get('page',1)
        pagesize = int(request.GET.get('pagesize',16))
        reverse = bool(int(request.GET.get('reverse',1)))           
                 
        alldata = []
        i=0
        job_key_list=redis_job_client.keys(config.prefix_job+'*')
        page_number = len(job_key_list)
        
        start = (int(page) - 1) * pagesize
        end = int(page) * pagesize

        for j in job_key_list:
            job_info=redis_job_client.hgetall(j)
            job_info['work_id']=j
        
            alldata.append(job_info)
        
        def sortitem(element):
            sort_keyname='begin_time'
            return element[sort_keyname] if sort_keyname in element else 0 
        
        alldata.sort(key=sortitem,reverse=reverse)    

        data=alldata[start:end]        
  
        return Response({'status':1,'data': data,'page': page_number})


class order(baseview.BaseView):
    '''
    :argument 执行工单详细信息的查询 删除 终止 

    '''
    @error_capture
    def get(self, request, args = None):

        if args=="detail":
            work_id = request.GET['workid']
            
            def get_summary(work_id):
                data=[]
                job_info=redis_log_client.hgetall(config.prefix_log+work_id)
                
                if (job_info):
                    for c in eval(job_info.get('log')):
                        x={}
                        x['target']=c[0].split('_'+c[0].split('_')[-1])[0]
                        x['target_id']=c[0].split('_')[-1]
                        x['playbook_rownum']=job_info.get('playbook_rownum')    
                        x['exe_rownum']=redis_log_client.llen(c[1])
                        
                        log_target_sum=redis_log_client.hgetall('sum_'+x['target_id'])
                        x['begin_date']=log_target_sum.get('begin_timestamp')
                        x['end_date']=log_target_sum.get('end_timestamp')
                        if x['begin_date'] and x['end_date']:
                            x['endure']=float(x['end_date'])-float(x['begin_date'])

                        if log_target_sum.get('stop_str'):
                            x['exe_status']=log_target_sum.get('stop_str')
                        else:
                            x['exe_status']='executing'

                        data.append(x)
                return data

            try:
                data=get_summary(work_id)
            except:
                return Response({'status':-1, 'msg':safe_decode('获取日志信息失败')})
            
            rerun_str=redis_log_client.hget(config.prefix_log+work_id,'rerun')
            if not rerun_str:
                rerun_str=''

            for r_work_id in rerun_str.split(','):
                r_data=get_summary(r_work_id)
                for i in data:
                    for j in r_data:
                        if i['target'] == j['target']:
                            data.remove(i)
                            data.append(j)
            
            playbook=redis_job_client.hget(work_id,'playbook')

            return Response({'status':1, 'data': data, 'playbook':playbook})


        elif args=='del':
            work_id = request.GET['workid']

            redis_job_client.delete(work_id)

            return Response({'status':1})


        elif args=='abort':
            target_id = request.GET['target_id']

            abort_time=redis_send_client.get(config.prefix_kill+target_id)
            if not abort_time:
                abort_time=str(time.time())

                redis_log_client.hset(config.prefix_sum+target_id,'stop_str','killing')

                redis_send_client.set(config.prefix_kill+target_id,abort_time)                
                #redis_send_client.expire('kill_'+target_id,60)

                return Response({'status':1,'abort_time':0})
            else:
                return Response({'status':-1,'abort_time':abort_time,'msg':safe_decode('已经存在终止操作')})
            
            
        elif args=='exelist':
            '''
            获取执行日志的id列表
            '''
            target_id = request.GET['id']

            target_id = config.prefix_log_target+target_id
            l_len=redis_log_client.llen(target_id)
            exelist=[]
            if l_len:
                exelist=redis_log_client.lrange(target_id,0,l_len-1)                

            return Response({'status':1,'exelist':exelist})
        

        elif args=='exedetail':
            '''
            获取单条命令的日志信息
            '''
            cmd_id = request.GET['id']
            
            exedetail=redis_log_client.hgetall(cmd_id)
            return Response({'status':1, 'exedetail':exedetail})            
            

        elif args=='summary':
            summary=[]
            job_id = request.GET['workid']
            
            log_target=redis_log_client.hget(config.prefix_log+job_id,'log')
        
            if log_target: 
                log_target_list=eval(log_target)
            else:
                log_target_list=[]


            job_rerun=redis_log_client.hget(config.prefix_log+job_id,'rerun')
            if job_rerun:
                for j in job_rerun.split(','):
                    log_target_list +=eval(redis_log_client.hget('log_'+j,'log'))   
                        

            tmp_summary={}
            for c in log_target_list:
                x = {}
                x['target'] = c[0].split('_'+c[0].split('_')[-1])[0]
                x['target_id']  = c[0].split('_')[-1]
                x['last_stdout'] = redis_log_client.hget(config.prefix_sum+x['target_id'],'last_stdout')          
                if not x['last_stdout']:
                    x['last_stdout'] = ''
                
                last_uuid= redis_log_client.hget(config.prefix_sum+x['target_id'],'last_uuid')
                if not last_uuid:                
                    pass
                elif not redis_log_client.hgetall(last_uuid):            
                    pass
                elif str(redis_log_client.hget(last_uuid,'exit_code')) != '0':
                    stderr=redis_log_client.hget(last_uuid,'stderr')
                    if stderr:
                        x['last_stdout'] = 'stderr: '+stderr
                    else:
                        x['last_stdout'] = 'stderr: null'
                tmp_summary[x['target']]=x

            for k in tmp_summary.keys():
                summary.append(tmp_summary[k])           

            return Response({'status':1,'data':summary})                               
