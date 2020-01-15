#coding:utf8
import os
import re
import sys
import yaml
import time
import redis
from threading import Thread
from multiprocessing import Process

from django.conf import settings

from libs import redis_pool
from conf import config
from .dura import Dura
from libs.util import MYLOGGER,MYLOGERROR


class SolveDura():
    '''
    根据实际情况对对应的key进行过期设置
    以及从mongodb同步到redis
    '''
    redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()

    def __init__(self, mongodb_config, dura_config='dura.conf', time_gap=60):
        BASE_DIR=os.path.dirname(os.path.abspath(__file__))
        self.yaml_file=os.path.join(BASE_DIR,dura_config)
        self.mongodb_config=mongodb_config
        self.dura = self.getDura(self.mongodb_config, self.yaml_file)

        self.time_gap=time_gap
        self.__background()
        
    
    def getDura(self, mongodb_config, yaml_file):
        
        redis_client_set=redis_pool.redis_init()
        with open(yaml_file,'rb') as f:
            if sys.version_info>(3,0):
                yaml_dict=yaml.load(f,Loader=yaml.FullLoader)
            else:
                yaml_dict=yaml.load(f)
        
        return Dura(yaml_dict, mongodb_config, redis_client_set)


    def get_keys(self, key):
        '''
        由log_job_XXXXXX 在redis中获取关联的key 只能用于过期设置
        '''
        job_id=key.split('_')[-1]
        #session
        #session_list=self.redis_tmp_client.keys('session_'+'*'+job_id)
        session_list=self.redis_tmp_client.keys(config.prefix_session+'*'+job_id)

        target_log_list=[]
        global_list=[]
        log_list=[]
        sum_list=[]
        target_list=[]

        #global_target_list=[]

        log_job_info=self.redis_log_client.hgetall(key)
        if 'log' in log_job_info:
            for tl in eval(log_job_info.get('log','[]')):
                target_list.append(tl[0])
                target_log=tl[1]
                target_id=target_log.split('_')[-1]
                target_log_list.append(target_log)
                global_list += self.redis_tmp_client.keys(config.prefix_global+target_id)
                #global_target_list += self.redis_tmp_client.keys('*'+target_id)
                sum_list    += self.redis_log_client.keys(config.prefix_sum+target_id)
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


    def __expire(self):
        '''
        监听执行日志log_job_XXXXXX，判定执行结束将对应关联key设置过期
        '''
        log_prefix=config.prefix_log+config.prefix_job
        while True:
            for k in self.redis_log_client.keys(log_prefix+'*'):
                
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
            for ck in client_key:
                redis_client=ck[0]
                for ik in ck[1]:
                    #过期的时间跟session的过期时间一致
                    redis_client.expire(ik, expire_time)
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
            for tl in eval(log_job_info.get('log','[]')):
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
            
            for ck in client_key:
                redis_client=ck[0]
                for ik in ck[1]:
                    x=self.dura.reload(ik, redis_client)
                    summary.append(x)

            return key,summary
        else:
            return None,None


    def __save(self):
        '''
        从redis保存数据到mongodb
        无限循环运行
        '''
        dura = self.getDura(self.mongodb_config, self.yaml_file)
        while True:
            dura.save()
            time.sleep(self.time_gap)


    def __load(self):
        '''
        mongodb数据自动加载到redis
        只在初始化时运行一次
        '''
        #mongodb client不能在多进程之间fork 因而在此重新实例化一个对象
        dura = self.getDura(self.mongodb_config, self.yaml_file)
        dura.load()


    def __background_t(self):
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


    def __background(self):
        p1=Process(target=self.__expire,args=())
        p2=Process(target=self.__save,args=())   
        t1=Thread(target=self.__load,args=())     
        p1.start()
        p2.start()
        t1.start()
        #启动时加载使用线程模式，防止存在僵死进程



try:
    MONGODB_CONFIG = settings.MONGODB_CONFIG
except:
    MONGODB_CONFIG=None

if MONGODB_CONFIG:
    #单例模式
    solve_dura=SolveDura(MONGODB_CONFIG)
else:
    MYLOGGER.info('no durability for MONGODB_CONFIG [ %s ] in settings ' % str(MONGODB_CONFIG))
    solve_dura=None
