# -*- coding: utf-8 -*- 

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
    
    redis_send,redis_log,redis_tmp,redis_config,redis_job,redis_manage = redis_init()


    def __getitem__(self,item):
        '''
        可以当成字典使用        
        每次获取前都判断是否可用，如果不可用，重新生成
        因为在sentinel模式重新连接可能出现不可以
        每次获取客户端都判断一次 还是出现连接不可用？
        
        client=getattr(self, item)
        client=rc.refresh(client,get_redis_config(item))
        '''

        #tcp连接依旧保持，底层实现连接保持？
        client=rc.redis_init(get_redis_config(item))
        return client


#单例模式
redis_single=RedisSingle()
