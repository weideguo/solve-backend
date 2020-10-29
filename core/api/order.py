# -*- coding: utf-8 -*- 
import ast
import time
import redis
from rest_framework.response import Response

from auth_new import baseview
from libs import util
from conf import config
from dura import solve_dura

from libs.redis_pool import redis_single
from libs.util import translate

class Order(baseview.BaseView):
    '''
    执行工单详细信息的查询 删除 终止 

    '''
    def post(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        if args == 'select':
            cmd_id = request.GET['id']
            select_list = request.data
            select_value = ' '.join(select_list)
            redis_send_client.rpush(config.prefix_select+config.spliter+cmd_id,select_value)
            redis_send_client.delete(config.prefix_select+'_all'+config.spliter+cmd_id)

            return Response({'status':1, 'select_str': select_value, 'keyid':cmd_id})


    def get(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        redis_log_client = redis_single['redis_log']
        redis_job_client = redis_single['redis_job']

        if not args:
            '''
            查询所有工单列表
            '''
            page = request.GET.get('page',1)
            pagesize = int(request.GET.get('pagesize',16))
            sort_keyname = request.GET.get('orderby','begin_time')
            reverse = bool(int(request.GET.get('reverse',1)))           
                 
            dura_flag=False    
            if dura_flag:
                data=[]
                # 配置持久化数据库时执行工单列表全部通过数据库查询 如mongodb
            else:
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
                    return float(element[sort_keyname]) if sort_keyname in element else 0 
                
                alldata.sort(key=sortitem,reverse=reverse)    
                
                data=alldata[start:end]        
    
            return Response({'status':1,'data': data,'page': page_number})


        if args=="detail":
            '''
            查询单个工单的详细
            '''
            work_id = request.GET['workid']
            
            #只获取没有运行成功的
            exclude =  request.GET.get('exclude','')

            def get_summary(work_id):
                data=[]
                #log_job_xxx 不存在则从mongodb加载到redis
                if solve_dura:
                    solve_dura.reload(config.prefix_log+work_id,0)

                job_info=redis_log_client.hgetall(config.prefix_log+work_id)
                
                if (job_info):
                    for c in ast.literal_eval(job_info.get('log')):
                        x={}
                        x['target']=c[0].split(config.spliter+c[0].split(config.spliter)[-1])[0]
                        x['target_id']=c[0].split(config.spliter)[-1]
                        x['playbook_rownum']=job_info.get('playbook_rownum')    
                        x['exe_rownum']=redis_log_client.llen(c[1])
                        
                        log_target_sum=redis_log_client.hgetall('sum_'+x['target_id'])
                        x['begin_date']=log_target_sum.get('begin_timestamp')
                        x['end_date']=log_target_sum.get('end_timestamp')
                        if x['begin_date'] and x['end_date']:
                            x['endure']=round(float(x['end_date'])-float(x['begin_date']),4)

                        if log_target_sum.get('stop_str'):
                            x['exe_status']=log_target_sum.get('stop_str')
                        else:
                            x['exe_status']='executing'

                        data.append(x)
                return data

            try:
                data=get_summary(work_id)
            except:
                return Response({'status':-1, 'msg':util.safe_decode(translate('get_log_info_failed',request))})
            
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
            debug_list=redis_job_client.hget(work_id,'debug_list')
            if debug_list:
                debug_list=ast.literal_eval(debug_list)
            else:
                debug_list=[0]

            exe_sum = {'executing': 0,'done': 0,'fail': 0,'all': 0}
            new_data = []
            for d in data:
                exe_sum['all'] += 1
                if ('exe_status' in d) and (d['exe_status']=='done'):
                    exe_sum['done'] += 1
                else:
                    new_data.append(d)
                    if not ('exe_status' in d) or (('exe_status' in d) and (d['exe_status']=='executing')):
                        exe_sum['executing'] += 1

            exe_sum['fail']=exe_sum['all'] - exe_sum['done'] - exe_sum['executing']

            if exclude:
                return Response({'status':1, 'data': new_data, 'playbook':playbook,'sum':exe_sum,'debug_list':debug_list})
            else:
                return Response({'status':1, 'data': data, 'playbook':playbook,'sum':exe_sum,'debug_list':debug_list})


        elif args=='del':
            '''
            删除单条工单信息
            '''
            work_id = request.GET['workid']

            redis_job_client.delete(work_id)
            if solve_dura:
                solve_dura.delete(config.prefix_log+work_id)
                solve_dura.real_delete(work_id,redis_job_client)

            return Response({'status':1})


        elif args=='abort':
            '''
            终止单个执行
            '''
            target_id = request.GET['target_id']

            abort_time=redis_send_client.get(config.prefix_kill+target_id)
            if not abort_time:
                abort_time=str(time.time())

                redis_log_client.hset(config.prefix_sum+target_id,'stop_str','killing')

                redis_send_client.set(config.prefix_kill+target_id,abort_time)                
                #redis_send_client.expire('kill_'+target_id,60)

                #处于断点执行时
                redis_send_client.rpush(config.prefix_block+target_id, 'abort')
                #设置较短的过期时间 因为通过阻塞获取
                redis_send_client.expire(config.prefix_block+target_id, 100)

                #判断select等待
                log_len=redis_log_client.llen(config.prefix_log_target+target_id)
                if log_len:
                    last_cmd_id = redis_log_client.lrange(config.prefix_log_target+target_id,log_len-1,log_len-1)[0]
                    step_info = redis_log_client.hget(last_cmd_id,'step')
                    if step_info == 'waiting select':
                        redis_send_client.rpush(config.prefix_select+config.spliter+last_cmd_id,' ')
                        redis_send_client.delete(config.prefix_select+'_all'+config.spliter+last_cmd_id)

                return Response({'status':1,'abort_time':0})
            else:
                return Response({'status':-1,'abort_time':abort_time,'msg':util.safe_decode(translate('abort_alread_exist',request))})
            
            
        elif args=='exelist':
            '''
            获取单个执行的命令id列表
            '''
            target_id = request.GET['id']

            target_id = config.prefix_log_target+target_id
            l_len=redis_log_client.llen(target_id)
            exelist=[]
            is_pause=0 
            if l_len:
                exelist=redis_log_client.lrange(target_id,0,l_len-1)
                #当前最后执行命令的信息为 {'stdout': 'pausing'} 则说明当前的执行处于阻塞模式
                tmp_last_info=redis_log_client.hgetall(exelist[-1])
                #if str(tmp_last_info.get('stdout')) == 'pausing':
                if tmp_last_info.get('stdout') == 'pausing':
                    is_pause=1
            else:
                is_pause=0                

            return Response({'status':1,'exelist':exelist,'pause':is_pause})
        

        elif args=='exedetail':
            '''
            获取单条命令的日志信息
            '''
            cmd_id = request.GET['id']
            
            exedetail=redis_log_client.hgetall(cmd_id)

            key_select_all=config.prefix_select+'_all'+config.spliter+cmd_id

            select_all_str=redis_send_client.get(key_select_all)
            if select_all_str:
                #使用空格分割（命令返回值不能存在额外的空格）
                if 'origin_cmd' in exedetail:
                    cmd=exedetail['origin_cmd']
                    try:
                        select_var=cmd.split('=')[0].strip().split(config.prefix_select+'.')[1].strip() 
                        return Response({'status':2, 'exedetail':exedetail, 'select':select_all_str.split(' '), 'select_var':select_var}) 
                    except:
                        return Response({'status':-1, 'msg':translate('not_select_error',request)})
                else:
                    return Response({'status':-2, 'msg':translate('not_origin_cmd',request)})
                
            else:
                return Response({'status':1, 'exedetail':exedetail})            
            

        elif args=='summary':
            '''
            获取单个工单的汇总信息 即所有执行最后一条命令的输出
            '''
            
            job_id = request.GET['workid']

            summary=[]
            log_target=redis_log_client.hget(config.prefix_log+job_id,'log')
        
            if log_target: 
                log_target_list=ast.literal_eval(log_target)
            else:
                log_target_list=[]


            job_rerun=redis_log_client.hget(config.prefix_log+job_id,'rerun')
            if job_rerun:
                for j in job_rerun.split(','):
                    log_target_list +=ast.literal_eval(redis_log_client.hget('log_'+j,'log'))   
                        

            tmp_summary={}
            for c in log_target_list:
                x = {}
                x['target'] = c[0].split(config.spliter+c[0].split(config.spliter)[-1])[0]
                x['target_id']  = c[0].split(config.spliter)[-1]
                last_uuid= redis_log_client.hget(config.prefix_sum+x['target_id'],'last_uuid')
                if last_uuid and redis_log_client.hgetall(last_uuid):
                    x['last_stdout']=redis_log_client.hget(last_uuid,'stdout')
                    x['last_stderr']=redis_log_client.hget(last_uuid,'stderr') 
                               
                x['last_stdout'] = x.get('last_stdout') or ''
                x['last_stderr'] = x.get('last_stderr') or ''

                tmp_summary[x['target']]=x

            for k in tmp_summary.keys():
                summary.append(tmp_summary[k])           

            return Response({'status':1,'data':summary})                               
