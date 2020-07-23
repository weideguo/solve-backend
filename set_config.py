# -*- coding: utf-8 -*- 

from conf import config

from libs.redis_pool import redis_single
redis_manage_client=redis_single['redis_manage']
#当不存在对应key时，以默认值初始化
if not redis_manage_client.keys(config.key_solve_config):
    origin_config=[
        ("job_types","config_job_types",
            set(["default","update","test"])),
        ("target_types","config_target_types",
            set(["host", "server", "cluster", "container"])),
        ("tmpl_const","config_tmpl_const", 
            {"name":"必须const开头 存储常量key的名字 由英文以及下划线组成"}),
        ("tmpl_realhost","config_tmpl_realhost", 
            {"name":"必须严格为 realhost_<ip>","ip":"与管理机网络互通的ip或者proxy:<proxy_mark>:<ip>" ,"user":"ssh登录以及执行命令账号" ,"passwd":"账号密码" ,"ssh_port":"ssh端口号","proxy":"使用的代理，不用代理设置为空。优先以ip为准。"}),
        ("tmpl_host","config_tmpl_host", 
            {"name":"host开头 以_分层级","realhost":"对应的真实主机realhost"}),
        ("tmpl_server","config_tmpl_server", 
            {"name":"执行对象的名称 以server开头 以_分隔层级","host":"host对象的名称" ,"const":"关联的常量"}),
        ("tmpl_cluster","config_tmpl_cluster", 
            {"name":"执行对象的名称 以cluster开头 以_分隔层级","db1":"db主","db2":"db从","web":"游戏服","site":"游戏集群的site值"}),
        ("tmpl_container","config_tmpl_container", 
            {"name":"container开头 以_分层级"})
        ]
 
    for c in origin_config:
        redis_manage_client.hset(config.key_solve_config,c[0],c[1]) 
        if isinstance(c[2],str):  
            redis_manage_client.set(c[1],c[2]) 

        if isinstance(c[2],list):
            for k in c[2]:
                redis_manage_client.rpush(c[1],k)

        if isinstance(c[2],set):
            for k in list(c[2]):
                redis_manage_client.sadd(c[1],k)

        if isinstance(c[2],dict):  
            redis_manage_client.hmset(c[1],c[2]) 

    print("set config done")        
else:
    print("config key exist, skip set config")  