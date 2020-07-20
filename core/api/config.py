#coding:utf8
import time
import redis
import uuid
import json
from rest_framework.response import Response

from auth_new import baseview
from libs import util
from conf import config

from libs.redis_pool import redis_single
from libs.util import translate

#只会运行一次
redis_manage_client=redis_single['redis_manage']

class Config(baseview.BaseView):
    """
    可以动态设置的配置信息
    """
    def get(self, request, args = None):
        redis_manage_client=redis_single['redis_manage']

        key=request.GET['key']

        key_name=redis_manage_client.hget(config.key_solve_config,key)
        if key_name:
            key_type=redis_manage_client.type(key_name)
        else:
            return Response({'status':-1,'data':'','msg':util.safe_decode(translate('key_not_exist',request))})            
        

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
            return Response({'status':-2,'data':'','msg':util.safe_decode(translate('redis_key_type_error',request))})
            

        return Response({'status':1,'data':data})

    def post(self, request, args = None):
        """
        提交的数据可以为 string list set hash格式，如果为string list set则需要明确指定格式
        提交时设置header Content-Type: application/json 
        """
        redis_manage_client=redis_single['redis_manage']

        key=request.GET['key']
        key_type=request.GET.get('type','hash')
        try:
            info = request.data.dict()
        except:
            info = request.data
        
        if not info:
            return Response({'status':-2,'msg':util.safe_decode(translate('not_commit_empty_info',request))})    

        #redis_manage_client=redis_single['redis_manage']

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
                return Response({'status':-1,'msg':util.safe_decode(translate('type_constrict',request))})  


        key_name=redis_manage_client.hget(config.key_solve_config,key)    
        if key_name:
            o_key_type=redis_manage_client.type(key_name)

            if o_key_type == key_type or (o_key_type=='none'):
                return update_config(info)
            else:
                return Response({'status':-2,'msg':util.safe_decode(translate('type_not_match',request))})  
        else:
            key_name=config.prefix_config+uuid.uuid1().hex
            redis_manage_client.hset(config.key_solve_config,key,key_name)
            return update_config(info)


        

        

            

