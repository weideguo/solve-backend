#coding:utf8
import re
import copy
import datetime
import redis
from rest_framework.response import Response

from auth_new.models import Account
from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import error_capture
from libs.wrapper import redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client

class Home(baseview.BaseView):
    '''
    首页的信息
    '''
    @error_capture 
    def get(self, request, args = None):
        if args == 'info': 
            info = {}
            info['user'] = Account.objects.count()
            info['order'] = len(redis_job_client.keys(config.prefix_job+'*'))
            info['exec'] = len(redis_manage_client.keys(config.prefix_exec+'*'))
            info['realhost'] = len(redis_config_client.keys(config.prefix_realhost+'*'))
            
            all_target = []

            target_types_key=redis_manage_client.hget(config.key_solve_config,config.target_types)
            # target_types=redis_manage_client.lrange(target_types_key,0,redis_manage_client.llen(target_types_key))
            target_types=redis_manage_client.smembers(target_types_key)

            all_target=[]
            for t in target_types:
                all_target += redis_config_client.keys(t+'*')

            real_all_target=[]
            for k in all_target:
                if not re.match('^\S{32}$',k.split(config.spliter)[-1]):
                    real_all_target.append(k)    

            info['target'] = len(real_all_target)
            return Response(info) 

            
        elif args == 'stats':
            job_list=redis_job_client.keys(config.prefix_job+'*')
            stats = {}
            time_gap=config.exe_stats_time_gap
            now_time = datetime.datetime.now()
            for i in reversed(range(time_gap)):
                tmp_date = (now_time +datetime.timedelta(days=-i)).strftime("%y-%m-%d")     
                stats[tmp_date] = {}


            for j in job_list:
                j_timestamp=redis_job_client.hget(j,'begin_time')
                #print j_timestamp
                j_time=datetime.datetime.fromtimestamp(float(j_timestamp)).strftime("%y-%m-%d")            
                if j_time in stats:
                    #stats[j_time]=stats[j_time]+1
                    job_type=redis_job_client.hget(j,'job_type')
                    if not job_type:
                        job_type='default'
                    tmp_dict=stats[j_time]
                    if not 'all' in tmp_dict:
                        tmp_dict['all']=0

                    if not job_type in tmp_dict:
                        tmp_dict[job_type]=0
                
                    tmp_dict['all']=tmp_dict['all']+1
                    tmp_dict[job_type]=tmp_dict[job_type]+1

                    stats[j_time]=tmp_dict
                   
            job_types_key=redis_manage_client.hget(config.key_solve_config,config.job_types)
            #job_types=redis_manage_client.lrange(job_types_key,0,redis_manage_client.llen(job_types_key))
            job_types=redis_manage_client.smembers(job_types_key)

            mytime=sorted(stats.keys())

            import copy
            all_types=list(copy.deepcopy(job_types))
            all_types.append(config.job_rerun)
            all_types.append('all')

            r={}
            r['time']=mytime
            r['stats']=stats
            r['types']=all_types
            for i in mytime:
                for t in all_types:
                    if not t in r:
                        r[t]=[]        
                
                    if t in stats[i]:
                        r[t].append(stats[i][t])
                    else:
                        r[t].append(0) 
          
            return Response(r)


#class Test(baseview.AnyLogin):
class Test(baseview.BaseView):
    '''
    测试
    '''
    @error_capture 
    def get(self, request, args = None):
        r={'a':'aaa'}
        return Response(r)