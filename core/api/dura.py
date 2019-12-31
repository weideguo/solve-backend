#coding:utf8
import time
import redis
from rest_framework.response import Response

from auth_new import baseview
from libs import util, redis_pool
from libs.wrapper import error_capture
from conf import config

redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()




class Dura(baseview.BaseView):
    '''
    持久化操作
    '''
    @error_capture
    def get(self, request, args = None):
        id = request.GET['id']
        #job_xxx
        #log_job_xxx
        #log_target_xxxx
        #xxx
        #sum_xxx
        #session_xxx   
        #target        ?是否要存

        return Response({'status':1,'id':id})



