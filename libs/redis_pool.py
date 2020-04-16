#coding:utf8

import redis

from libs.util import getcp
from libs.redis_conn import RedisConn

cp=getcp()
rc=RedisConn()


def get_redis_config(section):
    """
    将每个section的配置信息转成dict
    """
    db=int(cp.get(section,'db'))
    password=cp.get(section,'password')
    sentinels=[]
    service_name=''
    host=''
    port=0
    try:
        sentinels=eval(cp.get(section,'sentinels'))
        service_name=cp.get(section,'service_name')
    except:    
        host=cp.get(section,'host')
        port=int(cp.get(section,'port'))

    return {"db":db,"password":password,"sentinels":sentinels,"service_name":service_name,"host":host,"port":port}


def redis_init():
    """
    初始化连接
    """
    redis_send_client = rc.redis_init(get_redis_config('redis_send'))
    redis_log_client= rc.redis_init(get_redis_config('redis_log'))
    redis_tmp_client= rc.redis_init(get_redis_config('redis_tmp'))
    #不可清除以下redis的信息
    redis_config_client = rc.redis_init(get_redis_config('redis_config'))
    redis_job_client = rc.redis_init(get_redis_config('redis_job'))
    redis_manage_client = rc.redis_init(get_redis_config('redis_manage'))

    return redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client


def refresh(redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client):
    """
    判断连接断开则重连
    """
    redis_send_client = rc.refresh(redis_send_client,get_redis_config('redis_send'))
    redis_log_client= rc.refresh(redis_log_client,get_redis_config('redis_log'))
    redis_tmp_client= rc.refresh(redis_tmp_client,get_redis_config('redis_tmp'))
    #不可清除以下redis的信息
    redis_config_client = rc.refresh(redis_config_client,get_redis_config('redis_config'))
    redis_job_client = rc.refresh(redis_job_client,get_redis_config('redis_job'))
    redis_manage_client = rc.refresh(redis_manage_client,get_redis_config('redis_manage'))

    return redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client


class RedisSingle(object):
    
    redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = redis_init()

    def refresh(self):
        """
        重新刷新，用于确保获取到可用的客户端  
        """
        self.redis_send_client,self.redis_log_client,self.redis_tmp_client,self.redis_config_client,self.redis_job_client,self.redis_manage_client = \
            refresh(self.redis_send_client,self.redis_log_client,self.redis_tmp_client,self.redis_config_client,self.redis_job_client,self.redis_manage_client)

    def get_client(self):
        self.refresh()
        return self.redis_send_client,self.redis_log_client,self.redis_tmp_client,self.redis_config_client,self.redis_job_client,self.redis_manage_client

#单例模式
redis_single=RedisSingle()
