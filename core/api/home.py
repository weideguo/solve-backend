# -*- coding: utf-8 -*- 
import re
import copy
import datetime
import redis
from rest_framework.response import Response

from auth_new.models import Account
from auth_new import baseview
from libs import util
from libs.wrapper import set_sort_key
from conf import config


from libs.redis_pool import redis_single
#from libs.wrapper import redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client


class Home(baseview.BaseView):
    '''
    首页的信息
    '''
    def get(self, request, args = None):
        redis_config_client,redis_job_client,redis_manage_client=redis_single['redis_config'],redis_single['redis_job'],redis_single['redis_manage']
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
                if len(k.split(config.spliter))>=2 and re.match('^[a-zA-Z0-9]{32}$',k.split(config.spliter)[-1]):
                    continue
                
                real_all_target.append(k)    

            info['target'] = len(real_all_target)
            return Response(info) 

            
        elif args == 'stats':
            cache_key='query_cache_job'
            set_sort_key(redis_job_client, cache_key, config.prefix_job, 'begin_time', True)

            job_len=redis_job_client.llen(cache_key)

            job_list=redis_job_client.lrange(cache_key, 0, job_len-1)
            #job_list=redis_job_client.keys(config.prefix_job+'*')

            stats = {}
            time_gap=config.exe_stats_time_gap

            now_time = datetime.datetime.now()
            for i in reversed(range(time_gap)):
                tmp_date = (now_time +datetime.timedelta(days=-i)).strftime("%y-%m-%d")     
                stats[tmp_date] = {}

            job_types=set()
            for j in job_list:
                j_timestamp=redis_job_client.hget(j,'begin_time') or 0
                
                j_time=datetime.datetime.fromtimestamp(float(j_timestamp)).strftime("%y-%m-%d")            
                if j_time in stats:
                    job_type=redis_job_client.hget(j,'job_type') or 'default'

                    tmp_dict=stats[j_time]
                    tmp_dict['all']=tmp_dict.get('all',0)+1
                    tmp_dict[job_type]=tmp_dict.get(job_type,0)+1

                    stats[j_time]=tmp_dict
                    job_types.add(job_type)
                else:
                    break
            
            job_types.add('all')
            all_types=list(job_types)
            mytime=sorted(stats.keys())
            r={}
            #r['stats']=stats
            r['time']=mytime
            r['types']=all_types
            for t in all_types:
                r[t]=[]  

            for i in mytime:
                for t in all_types:
                    r[t].append(stats[i].get(t,0))
          
            return Response(r)


