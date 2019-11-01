#coding:utf8

import redis

from libs.util import getcp


cp=getcp()

redis_send_pool=redis.ConnectionPool(host=cp.get('redis_send','host'), port=int(cp.get('redis_send','port')), db=int(cp.get('redis_send','db')), password=cp.get('redis_send','passwd'), decode_responses=True)

redis_log_pool=redis.ConnectionPool(host=cp.get('redis_log','host'), port=int(cp.get('redis_log','port')), db=int(cp.get('redis_log','db')), password=cp.get('redis_log','passwd'), decode_responses=True)

#不可清除以下redis的信息
redis_config_pool=redis.ConnectionPool(host=cp.get('redis_config','host'), port=int(cp.get('redis_config','port')), db=int(cp.get('redis_config','db')), password=cp.get('redis_config','passwd'), decode_responses=True)

redis_job_pool=redis.ConnectionPool(host=cp.get('redis_job','host'), port=int(cp.get('redis_job','port')), db=int(cp.get('redis_job','db')), password=cp.get('redis_job','passwd'), decode_responses=True)

redis_manage_pool=redis.ConnectionPool(host=cp.get('redis_manage','host'), port=int(cp.get('redis_manage','port')), db=int(cp.get('redis_manage','db')), password=cp.get('redis_manage','passwd'), decode_responses=True)

def redis_init():
    redis_send_client = redis.StrictRedis(connection_pool=redis_send_pool)
    redis_log_client=redis.StrictRedis(connection_pool=redis_log_pool)
    redis_config_client = redis.StrictRedis(connection_pool=redis_config_pool)
    redis_job_client = redis.StrictRedis(connection_pool=redis_job_pool)
    redis_manage_client = redis.StrictRedis(connection_pool=redis_manage_pool)

    return redis_send_client,redis_log_client,redis_config_client,redis_job_client,redis_manage_client


