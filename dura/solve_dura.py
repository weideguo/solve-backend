# -*- coding: utf-8 -*- 
import os
import re
import ast
import sys
import yaml
import time
import redis
from threading import Thread
from multiprocessing import Process

base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from pymongo.errors import PyMongoError,ServerSelectionTimeoutError
from redis.exceptions import ConnectionError
from django.conf import settings

from libs import redis_pool,util
from conf import config
from libs.util import MYLOGGER,MYLOGERROR
from .dura import Dura

def connection_error_rerun(retry_gap=5):
    """
    当发生连接错误时函数的重新运行
    """
    def __wrapper(func):                  
        def __wrapper2(*args, **kwargs):
            while True:
                try:
                    func(*args, **kwargs)
                    break
                except (ConnectionError,PyMongoError,ServerSelectionTimeoutError):
                    time.sleep(retry_gap)
                    if args:
                        func_name="%s.%s" % (args[0].__class__.__name__, func.__name__)
                    else:
                        func_name=func.__name__
                    
                    MYLOGERROR.error("function:%s  retry" % func_name)
                          
        return __wrapper2
    return __wrapper


class SolveDura():
    '''
    根据实际情况对对应的key进行过期设置
    以及从mongodb同步到redis
    '''
    redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client=redis_pool.redis_init()

    def __init__(self, mongodb_config, dura_config='dura.conf', time_gap=60):
        BASE_DIR=os.path.dirname(os.path.abspath(__file__))
        self.yaml_file=os.path.join(BASE_DIR,dura_config)
        self.mongodb_config=mongodb_config
        self.dura = self.getDura()

        self.time_gap=time_gap
        # self.__background()
    

    def redis_refresh(self):
        self.redis_send_client,self.redis_log_client,self.redis_tmp_client,self.redis_config_client,self.redis_job_client,self.redis_manage_client = \
                redis_pool.refresh(self.redis_send_client,self.redis_log_client,self.redis_tmp_client,self.redis_config_client,self.redis_job_client,self.redis_manage_client)


    def getDura(self):
        
        redis_client_set=redis_pool.redis_init()
        with open(self.yaml_file,'rb') as f:
            if sys.version_info>(3,0):
                yaml_dict=yaml.load(f,Loader=yaml.FullLoader)
            else:
                yaml_dict=yaml.load(f)
        
        return Dura(yaml_dict, self.mongodb_config, redis_client_set)


    def get_keys(self, key):
        '''
        由log_job_XXXXXX 在redis中获取关联的key 只能用于过期设置
        '''
        job_id=key.split('_')[-1]
        #session
        #session_list=self.redis_tmp_client.keys('session_'+'*'+job_id)
        session_list = list(self.redis_tmp_client.scan_iter(config.prefix_session+'*'+job_id))

        target_log_list=[]
        global_list=[]
        log_list=[]
        sum_list=[]
        target_list=[]

        #global_target_list=[]

        log_job_info=self.redis_log_client.hgetall(key)
        if 'log' in log_job_info:
            #for tl in eval(log_job_info.get('log','[]')):
            for tl in ast.literal_eval(log_job_info.get('log','[]')):
                target_list.append(tl[0])
                target_log=tl[1]
                target_id=target_log.split('_')[-1]
                target_log_list.append(target_log)
                global_list += list(self.redis_tmp_client.scan_iter(config.prefix_global+target_id))
                #global_target_list += self.redis_tmp_client.keys('*'+target_id)
                sum_list    += list(self.redis_log_client.scan_iter(config.prefix_sum+target_id))
                log_list    += self.redis_log_client.lrange(target_log, 0, self.redis_log_client.llen(target_log))


        return target_log_list, sum_list, log_list, session_list, global_list, target_list


    def is_job_finish(self,target_log_list, sum_list):
        '''
        由log_job_XXXXXX 获取关联的log_target_YYY以及sum_YYY判定任务是否执行结束
        '''
        if len(target_log_list) == len(sum_list):
            for l in sum_list:
                if not ('stop_str' in self.redis_log_client.hgetall(l)):
                    #print(l)
                    return False

            #所有的sum_YYY都存在'stop_str'属性时则表明任务执行完毕
            return True
        else:
            #print(len(target_log_list),len(sum_list))
            return False


    @connection_error_rerun()
    def __expire(self):
        '''
        监听执行日志log_job_XXXXXX，判定执行结束将对应关联key设置过期
        '''
        self.redis_refresh()
        log_prefix=config.prefix_log+config.prefix_job
        while True:
            for k in self.redis_log_client.scan_iter(log_prefix+'*'):
                
                if self.redis_log_client.ttl(k) <= 0:
                    self.expire(k)
                    #print('expire %s'  % k)
            MYLOGGER.info('set keys expire done')
            time.sleep(self.time_gap)
    

    def expire(self, key, force=0, expire_time=config.tmp_config_expire_sec):
        '''
        单个log_job_XXX的过期设置
        force 是否不管已经完成与否，默认需要完成才设置过期
        设置过期前要检查ttl，否则过期时间会重置，导致没有弹出redis
        '''
        target_log_list, sum_list, log_list, session_list, global_list, target_list = self.get_keys(key)

        client_key = [(self.redis_log_client, [key]+target_log_list+log_list+sum_list),\
                      (self.redis_tmp_client, session_list+global_list+target_list)]

        if self.is_job_finish(target_log_list, sum_list) or force:
            for redis_client,k_list in client_key:
                for k in k_list:
                    #过期的时间跟session的过期时间一致
                    redis_client.expire(k, expire_time)
                    #print(str(redis_client), ik, str(config.tmp_config_expire_sec))
            return client_key
        else:
            return None
    

    def get_key_info_from_mongo(self, redis_client, key=None, pattern=None):
        '''
        从mongodb获取key的信息
        '''
        key_info={}
        if key:
            connection_name=self.dura.get_collection_name(key, redis_client)
            if connection_name:
                key_info = self.dura.db[connection_name].find({self.dura.primary_key: key})
        elif pattern:
            connection_name=self.dura.get_collection_name(pattern, redis_client)
            if connection_name:
                key_info=self.dura.db[connection_name].find({self.dura.primary_key: {'$regex': pattern}})
                
        try:
            key_info=key_info[0]
        except:
            key_info={}
        return key_info


    def get_keys_from_mongo(self, key):
        '''
        由log_job_XXXXXX 在mongodb中获取关联的key 用于从mongodb加载到redis
        '''
        target_log_list = []
        sum_list = []
        log_list = []
        session_list = []
        global_list = []
        target_list = []

        job_id=key.split('_')[-1]

        job_info=self.get_key_info_from_mongo(self.redis_job_client,config.prefix_job+job_id)
        if 'target_type' in job_info:
        	target_type=job_info['target_type']
        else:
        	target_type=''

        session_pattern=config.prefix_session+'.*_'+job_id
        session_list_info=self.get_key_info_from_mongo(self.redis_tmp_client, pattern=session_pattern)

        if self.dura.primary_key in session_list_info:
            session_list.append(session_list_info[self.dura.primary_key])

        log_job_info=self.get_key_info_from_mongo( self.redis_log_client, key)

        if 'log' in log_job_info:
            #for tl in eval(log_job_info.get('log','[]')):
            for tl in ast.literal_eval(log_job_info.get('log','[]')):
                target_log=tl[1]
                target_id=target_log.split('_')[-1]
                target_log_list.append(target_log)
                
                global_list.append(config.prefix_global+target_id)

                target_pattern=target_type+'.*_'+target_id
                target_list_info=self.get_key_info_from_mongo(self.redis_tmp_client, pattern=target_pattern)
        
                if self.dura.primary_key in target_list_info:
                    target_list.append(target_list_info[self.dura.primary_key])

                sum_list.append(config.prefix_sum+target_id,)

                log_list_info = self.get_key_info_from_mongo( self.redis_log_client, target_log)
                if self.dura.list_name in log_list_info and isinstance(log_list_info[self.dura.list_name],list):
                    log_list += log_list_info[self.dura.list_name]

        return target_log_list, sum_list, log_list, session_list, global_list, target_list


    def reload(self, key, is_update=1):
        '''
        key 由log_job_XXXXXX 从mongodb加载相关key到redis
        is_update 0 redis中存在时跳过 1 强制从mongodb加载到redis
        '''
        summary=[]
        key_exist=self.redis_log_client.exists(key)
        if (not key_exist) or is_update:
            #redis中不存在，或者强制为更新，则都mongodb加载
            #self.dura.load(key, self.redis_log_client)
            target_log_list, sum_list, log_list, session_list, global_list, target_list = self.get_keys_from_mongo(key)
    
            client_key = [(self.redis_log_client, [key]+target_log_list+log_list+sum_list),\
                          (self.redis_tmp_client, session_list+global_list+target_list)]
            
            for redis_client,k_list in client_key:
                for k in k_list:
                    r=self.dura.reload(k, redis_client)
                    summary.append(r)

            return key,summary
        else:
            return None,None


    def delete(self, key):
        '''
        在mongodb删除对应key的信息，log_job_xxx获取关联key并删除
        '''
        target_log_list, sum_list, log_list, session_list, global_list, target_list = self.get_keys(key)

        client_key = [(self.redis_log_client, [key]+target_log_list+log_list+sum_list),\
                      (self.redis_tmp_client, session_list+global_list+target_list)]


        for redis_client,k_list in client_key:
            for k in k_list:
                #print("delete in mongodb for %s %s" % (str(redis_client),str(k)))
                try:
                    self.real_delete(k, redis_client)
                except:
                    pass

        return client_key


    def real_delete(self, key, redis_client):
        '''
        在mongodb删除对应key的信息 任意key的删除
        '''
        redis_client.delete(key)
        connection_name=self.dura.get_collection_name(key, redis_client)
        r=self.dura.db[connection_name].delete_many({self.dura.primary_key: key})
        #print(connection_name,{self.dura.primary_key: key})
        #{'ok': 1.0, 'n': 0}
        #{'ok': 1.0, 'n': 1}
        #if 'n' in r and r['n']:
        #DeleteResult({'n': 0, 'ok': 1.0}, acknowledged=True)
        if r.deleted_count:
            return key
        else:
            return None


    @connection_error_rerun()
    def __save(self):
        '''
        从redis保存数据到mongodb
        无限循环运行
        '''
        self.redis_refresh()
        dura = self.getDura()
        while True:
            dura.save()
            time.sleep(self.time_gap)


    def __load(self):
        '''
        mongodb数据自动加载到redis
        只在初始化时运行一次
        '''
        #mongodb client不能在多进程之间fork 因而在此重新实例化一个对象
        dura = self.getDura()
        dura.load()


    def background_t(self):
        '''
        线程模型 
        GIL Global Interpreter Lock
        存在全局锁导致只能使用一个CPU核心？
        '''
        t1=Thread(target=self.__expire,args=())
        t2=Thread(target=self.__save,args=())   
        t3=Thread(target=self.__load,args=())     
        t1.start()
        t2.start()
        t3.start()


    def background(self):
        p1=Process(target=self.__expire,args=())
        p2=Process(target=self.__save,args=())   
        t1=Thread(target=self.__load,args=())     
        p1.start()
        p2.start()
        t1.start()
        #启动时加载使用线程模式，防止存在僵死进程


class BaseDura():
    def get_keys(self, *arg, **kwargs): 
        pass
    def reload(self, *arg, **kwargs):
        pass
    def expire(self, *arg, **kwargs):
        pass
    def delete( *arg, **kwargs):
        pass
    def real_delete(self, *arg, **kwargs):
        pass
    def background_t(self, *arg, **kwargs):
        pass
    def background(self, *arg, **kwargs):
        pass



MONGODB_CONFIG={}
cp=util.getcp()
if cp.has_section('mongodb') and cp.has_option('mongodb','uri') and cp.has_option('mongodb','db'):
    MONGODB_CONFIG['uri']=cp.get('mongodb','uri')
    MONGODB_CONFIG['db']=cp.get('mongodb','db')

if MONGODB_CONFIG:
    #单例模式
    MYLOGGER.info('durability for MONGODB_CONFIG [ %s ] in settings ' % str(MONGODB_CONFIG))
    solve_dura=SolveDura(MONGODB_CONFIG)
else:
    MYLOGGER.info('no durability for MONGODB_CONFIG [ %s ] in settings ' % str(MONGODB_CONFIG))
    solve_dura=BaseDura()

