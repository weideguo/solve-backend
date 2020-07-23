# -*- coding: utf-8 -*- 
from  threading import Thread
import time
from redis.exceptions import ConnectionError
from traceback import print_exc

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from libs.redis_pool import redis_single
    
#redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_single.get_client()

def f(client):
    while True:
        try:
            x=client["redis_send"].ping()
            #print(x)
        except ConnectionError:
            print_exc()
            
        time.sleep(5)
 
 
if __name__ == "__main__":
    """
    测试高并发下的连接问题
    sentinel断开后重连出现错误
    """
    t_list=[]
    for i in range(10):
        t=Thread(target=f,args=(redis_single,))
        t_list.append(t)
    
    
    for t in t_list:
        t.start()
        



