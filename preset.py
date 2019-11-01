#!/bin/env python
#coding:utf8
import os
import configparser
import redis


solve_config="solve_config"
config=[
        ("job_types","config_qrkueihtklhoiuou",["default","update","test","rerun"]),
        ("target_types","config_qrkueihtklhoiuou111",["host", "server", "cluster", "container"]),
        ("tmpl_const","config_tmpl_const", {"name":"必须const开头 存储常量key的名字 由英文以及下划线组成"}),
        ("tmpl_realhost","config_tmpl_realhost", {"ip":"与管理机网络互通的ip" ,"user":"ssh登录以及执行命令账号" ,"passwd":"账号密码" ,"ssh_port":"ssh端口号","name":"必须严格为 realhost_<ip>"}),
        ("tmpl_host","config_tmpl_host", {"name":"host开头 以_分层级","realhost":"对应的真实主机realhost"}),
        ("tmpl_server","config_tmpl_server", {"name":"执行对象的名称 以server开头 以_分隔层级","host":"host对象的名称" ,"const":"关联的常量"}),
        ("tmpl_cluster","config_tmpl_cluster", {"name":"执行对象的名称 以cluster开头 以_分隔层级","db1":"db主","db2":"db从","web":"游戏服","site":"游戏集群的site值"}),
        ("tmpl_container","config_tmpl_container", {"name":"container开头 以_分层级"})
        ]


#############################################################################################################################################################
def getcp():
    cp = configparser.ConfigParser()
    cp.read('deploy.conf')
    return cp

def redis_set():
    cp=getcp()
    redis_manage_pool=redis.ConnectionPool(host=cp.get('redis_manage','host'), port=int(cp.get('redis_manage','port')),\
                     db=int(cp.get('redis_manage','db')), password=cp.get('redis_manage','passwd'), decode_responses=True)
    
    redis_manage_client=redis.StrictRedis(connection_pool=redis_manage_pool)
    

    for c in config:
        redis_manage_client.hset(solve_config,c[0],c[1]) 
        if isinstance(c[2],str):  
            redis_manage_client.set(c[1],c[2]) 
        if isinstance(c[2],list):
            for k in c[2]:
                redis_manage_client.rpush(c[1],k) 
        if isinstance(c[2],dict):  
            redis_manage_client.hmset(c[1],c[2]) 


def file_root_set():
    cp=getcp()
    file_root=cp.get('common','file_root')
    os.makedirs(file_root)
    return file_root



if __name__ == "__main__":
    print("-----------------------------------------redis set begin-----------------------------------------")
    redis_set()
    print("-----------------------------------------redis set success-----------------------------------------")

    print("-----------------------------------------make dirs-----------------------------------------")
    r=file_root_set()
    print("-----------------------------------------make dirs success: %s -----------------------------------------" % r)


