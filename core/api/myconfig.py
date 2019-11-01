#coding:utf8
import time
import redis
from rest_framework.response import Response

from libs import baseview, util, redis_pool
from libs.util import error_capture,safe_decode
from conf import config

redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()

class myconfig(baseview.BaseView):
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
            return Response({'status':-1,'data':'','msg':safe_decode('key不存在')})            
        

        data=None
        if key_type=='list':
            data=redis_manage_client.lrange(key_name,0,redis_manage_client.llen(key_name))
        elif key_type=='hash':
            data=redis_manage_client.hgetall(key_name)
        elif key_type=='string':
            data=redis_manage_client.get(key_name)         
        else:
            return Response({'status':-2,'data':'','msg':safe_decode('key在redis中的存储类型错误')})
            

        return Response({'status':1,'data':data})        

