#coding:utf8
import time
import redis
import uuid
import json
from rest_framework.response import Response

from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import error_capture
#from libs.wrapper import redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client
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


class Config(baseview.BaseView):
    """
    可以动态设置的配置信息
    """
    @error_capture
    def get(self, request, args = None):
        key=request.GET['key']

        #为什么在此容易出现客户端使用失败？需要每次都重新获取
        redis_manage_client=redis_single['redis_manage']
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


        

        

            

