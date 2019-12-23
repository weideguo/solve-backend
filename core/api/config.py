#coding:utf8
import time
import redis
import uuid
import json
from rest_framework.response import Response

from auth_new import baseview
from libs import util, redis_pool
from libs.wrapper import error_capture
from conf import config

redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()

class Config(baseview.BaseView):
    """
    可以动态设置的配置信息
    """
    @error_capture
    def get(self, request, args = None):
        key=request.GET['key']

        key_name=redis_manage_client.hget(config.key_solve_config,key)
        if key_name:
            key_type=redis_manage_client.type(key_name)
        else:
            return Response({'status':-1,'data':'','msg':util.safe_decode('key不存在')})            
        

        data=None
        if key_type=='list':
            data=redis_manage_client.lrange(key_name,0,redis_manage_client.llen(key_name))
        elif key_type=='set':
            data=redis_manage_client.smembers(key_name)
        elif key_type=='hash':
            data=redis_manage_client.hgetall(key_name)
        elif key_type=='string':
            data=redis_manage_client.get(key_name)         
        else:
            return Response({'status':-2,'data':'','msg':util.safe_decode('key在redis中的存储类型错误')})
            

        return Response({'status':1,'data':data})

    @error_capture
    def post(self, request, args = None):
        """
        提交的数据可以为 string list set hash格式，如果为string list set则需要明确指定格式
        提交时设置header Content-Type: application/json 
        """
        key=request.GET['key']
        key_type=request.GET.get('type','hash')
        try:
            info = request.data.dict()
        except:
            info = request.data
        
        if not info:
            return Response({'status':-2,'msg':util.safe_decode('提交信息不能为空')})    


        def update_config(info):
            if key_type == 'list':
                # 可以直接获取list格式的数据
                redis_manage_client.delete(key_name)
                for k in info:
                    redis_manage_client.rpush(key_name,k)

                return Response({'status':1,'key':key,'type':key_type,'data':info})
            elif key_type == 'set':    
                redis_manage_client.delete(key_name)
                for k in info:
                    redis_manage_client.sadd(key_name,k)

                return Response({'status':1,'key':key,'type':key_type,'data':info})
            elif key_type == 'string':
                #Content-Type: application/x-www-form-urlencoded
                info=info.keys()[0]
                redis_manage_client.set(key_name,info)
                return Response({'status':1,'key':key,'type':key_type,'data':info})
            elif key_type == 'hash':
                redis_manage_client.delete(key_name)
                redis_manage_client.hmset(key_name,info)
                return Response({'status':1,'key':key,'type':key_type,'data':info})
            else:
                return Response({'status':-1,'msg':util.safe_decode('type必须为string list set hash之一')})  


        key_name=redis_manage_client.hget(config.key_solve_config,key)    
        if key_name:
            o_key_type=redis_manage_client.type(key_name)

            if o_key_type == key_type or (o_key_type=='none'):
                return update_config(info)
            else:
                return Response({'status':-2,'msg':util.safe_decode('type类型不匹配')})  
        else:
            key_name=config.prefix_config+uuid.uuid1().hex
            redis_manage_client.hset(config.key_solve_config,key,key_name)
            return update_config(info)


        

        

            

