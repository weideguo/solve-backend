#coding:utf8
import re
import redis
import json
import time
import uuid
from rest_framework.response import Response

from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import HashCURD
from libs.redis_pool import redis_single


class Target(baseview.BaseView):
    '''
    执行对象的增删改查 
    '''    
    def get(self, request, args = None):
        redis_config_client = redis_single['redis_config']
        return HashCURD.get(redis_config_client,request, args)

    def post(self, request, args = None):
        redis_config_client = redis_single['redis_config']
        return HashCURD.post(redis_config_client,request, args)


class Host(baseview.BaseView):
    '''
    主机
    '''
    def get(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        redis_log_client = redis_single['redis_log']
        redis_config_client = redis_single['redis_config']

        def get_online():
            online_host = redis_send_client.keys(config.prefix_heart_beat+'*')    
            real_online_host = []
            current_timestamp = time.time()
            for h in online_host:
                timestamp_gap=current_timestamp-float(redis_send_client.get(h))
                #在此以心跳间隔超过判断为断开
                if timestamp_gap < config.host_check_success_time:
                    is_conn=1
                else:
                    is_conn=0
                real_online_host.append({'host':h.split(config.prefix_heart_beat)[1],'timestamp_gap':timestamp_gap,'is_conn':is_conn})
            return real_online_host    

        if args=='online': 
            return Response({'status':1,'data':get_online()})
    

        elif args=='onlinedetail':
            real_online_list=[]
            for online in get_online():
                a={}
                a['name']=config.prefix_realhost+online['host']
                a['is_conn']=online['is_conn']
                real_online_info=redis_config_client.hgetall(a['name'])
                real_online_info.update(a)
                real_online_list.append(real_online_info)

            page_number=len(real_online_list)
            return Response({'status':1, 'data': real_online_list,'page': page_number})


        elif args=='kill':
            ip = request.GET['ip']
            redis_send_client.rpush(config.key_conn_control,config.pre_close+ip)
            
            kill_counter=0
            while redis_send_client.get(config.prefix_heart_beat+ip) and kill_counter<100:
                time.sleep(0.1)
                kill_counter=kill_counter+1       
            
            if kill_counter<100:
                deletelist = redis_send_client.keys('*'+ip+'*')
                for d in deletelist:
                    redis_send_client.delete(d)
                return  Response({'status':1, 'msg':util.safe_decode('断开成功'), 'delete_list':deletelist}) 
            else:
                return  Response({'status':-1, 'msg':util.safe_decode('断开失败')})

        
        elif args=='conn': 
            ip = request.GET['ip']
            conn_uuid=uuid.uuid1().hex
            redis_send_client.rpush(config.key_conn_control,ip+config.spliter+conn_uuid)
            
            conn_counter=0        
            while not redis_send_client.get(config.prefix_heart_beat+ip) and conn_counter<100 and (not redis_log_client.hget(conn_uuid,'exit_code')):
                time.sleep(0.1)
                conn_counter=conn_counter+1

            exit_code=redis_log_client.hget(conn_uuid,'exit_code')
            if exit_code=='0':
                return  Response({'status':1, 'msg':util.safe_decode('连接成功')})
            elif exit_code:
                return  Response({'status':-1, 'msg': util.safe_decode(exit_code)})
            elif conn_counter<100:
                return  Response({'status':1, 'msg':util.safe_decode('连接成功')})
            else:
                return  Response({'status':-2, 'msg':util.safe_decode('连接超时')})

