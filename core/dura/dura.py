#coding:utf8
import os
import re
import sys
import time
import redis
import yaml
from threading import Thread

from django.conf import settings
from pymongo import MongoClient 

from libs import redis_pool

from libs.util import MYLOGGER,MYLOGERROR


class Dura():
    '''
    持久化操作
    '''

    def __init__(self, key_map_config, mongodb_config, time_gap=60):
        '''
        key_map_config   redis key与mongodb映射关系
        mongodb_config   mongodb的配置
        time_gap         redis同步到mongodb的时间间隔
        '''

        self.key_map_config = key_map_config
        self.primary_key = 'pid'       #存放在mongodb时的主键名，对应值为redis的key名
        self.list_name = 'key_list'    #redis的key为list时存储在mongodb的字段

        #pymongo内置连接池，可以自动处理网络波动问题，阻塞等待
        conn=MongoClient(host=mongodb_config['host'], port=mongodb_config['port'])
        self.db=conn[mongodb_config['db']]
        if ('user' in mongodb_config) and mongodb_config['user']:
            self.db.authenticate(mongodb_config['user'], mongodb_config['passwd']) 

        self.time_gap = time_gap
        self.__backgroup()


    def __save(self):
        '''
        从redis保存数据到mongodb
        '''
        while True:
            for db_config in self.key_map_config['save']:
                dbid=list(db_config.keys())[0]
                
                #获取对应的redis_client
                for c in redis_pool.redis_init():
                    if str(c).split(',db=')[-1].split('>')[0] == str(dbid):
                        redis_client=c

                #可能太大 使用scan代替
                for k in redis_client.keys():        
                    for key_config in db_config[dbid]:
                        collection_name = key_config['collection']
                        if re.match(key_config['key_pattern'], k):
                            value = {}
                            exist_count = self.db[collection_name].find({self.primary_key: k}).count()
                            key_type = redis_client.type(k)
                            #if key_config['type'] == 'hash':
                            if key_type == 'hash':
                                value = redis_client.hgetall(k)
                                value[self.primary_key] = k
                                # 根据pid判定是否存在，存在则更改，不存在则插入
                                # 设置update为0则没有更新操作
                                #if exist_count and (not key_config.get('update',1)):
                                #    print('not update -------%s %s' % (str(key_config),k))
                                if exist_count and key_config.get('update',1):
                                    self.db[collection_name].update({self.primary_key: k}, value)
                                elif not exist_count:
                                    self.db[collection_name].insert(value)
                                
                            #elif key_config['type'] == 'list':
                            elif key_type == 'list':    
                                all_list = redis_client.lrange(k,0,redis_client.llen(k))

                                #根据原有list的最后一个值 截取从redis获取的list 只插入新增加的
                                #redis中list不能只删除最后一个！！！否则这里会出错
                                if exist_count:
                                    #获取对应记录中list的最后一个值 返回list格式
                                    key_list=self.db[collection_name].find({self.primary_key: k},{ self.list_name: { '$slice': -1 }})[0].get(self.list_name, [])
                                    
                                    i=0
                                    if key_list:
                                        for rk in all_list:
                                            i=i+1
                                            if rk==key_list[-1]:
                                                break
                                        #如果都不匹配 则新redis的list需要全部插入到mongodb
                                        if not key_list[-1] in all_list:
                                            i=0

                                    new_list=all_list[i:]
                                    #print('save key -------%s %s  %s' % (new_list, k, str(i)))

                                    self.db[collection_name].update({self.primary_key: k},{'$push':{self.list_name: {'$each': new_list}}})
                                    #for nk in new_list:
                                    #    self.db[collection_name].update({self.primary_key: k},{'$push':{self.list_name:nk}})

                                else:
                                    value[self.list_name]=all_list
                                    value[self.primary_key] = k
                                    self.db[collection_name].insert(value)
                                
                    #print('save key ------- '+k)

            #print('save key from redis to mongodb')
            MYLOGGER.info('save key from redis to mongodb done')
            time.sleep(self.time_gap)


    def x__load(self):
        pass


    def __load(self):
        '''
        mongodb数据自动加载到redis
        只在初始化时进行一次
        '''
        for db_config in self.key_map_config['load']:
            dbid=list(db_config.keys())[0]
                
            #获取对应的redis_client
            for c in redis_pool.redis_init():
                if str(c).split(',db=')[-1].split('>')[0] == str(dbid):
                    redis_client=c

            for key_config in db_config[dbid]:
                collection_name = key_config['collection']
                self.real_load(redis_client, collection_name)
                #print(redis_client, collection_name)
                MYLOGGER.info('load collection [ %s ] from mongodb to redis done' % collection_name)



    def load(self, key, redis_client=None, dbid=0 ):
        '''
        单个key加载，对外提供接口
        使用save模块的配置
        '''
        if not redis_client:
            for c in redis_pool.redis_init():
                if str(c).split(',db=')[-1].split('>')[0] == str(dbid):
                    redis_client=c
        else:
            dbid = str(redis_client).split(',db=')[-1].split('>')[0]
            dbid = int(dbid)          

        for db_config in self.key_map_config['save']:
            if list(db_config.keys())[0] == dbid:
                for key_config in db_config[dbid]:
                    if re.match(key_config['key_pattern'],key):
                        collection_name=key_config['collection']

        self.real_load(redis_client, collection_name, {self.primary_key: key})
        
        #print(redis_client, collection_name, {self.primary_key: key})
        return collection_name, {self.primary_key: key}



    def real_load(self, redis_client, collection_name, find=None):
        '''
        实际从mongodb加载数据到redis
        '''
        for key_info in self.db[collection_name].find(find):
            
            key_name=key_info.pop(self.primary_key, '')
            if key_name:
                key_info.pop('_id', '')
                if ('key_list' in key_info) and (isinstance(key_info['key_list'],list)):
                    pipe = redis_client.pipeline()
                    for ki in key_info['key_list']:
                        pipe.rpush(key_name, ki)
                    pipe.execute()
                else:
                    redis_client.hmset(key_name, key_info)
                
            else:
                MYLOGERROR.error('key info error, \'%s\' not in %s at collection %s' % (self.primary_key, str(key_info), collection_name))


    def __backgroup(self):
        '''
        后台运行
        无限循环同步
        首次启动加载
        '''
        t1=Thread(target=self.__save,args=())   
        t2=Thread(target=self.__load,args=())   
        t1.start()
        t2.start()


def getDura(dura_config='core/dura/dura.conf'):
    try:
        MONGODB_CONFIG = settings.MONGODB_CONFIG
    except:
        MONGODB_CONFIG=None
    
    if MONGODB_CONFIG:
        yaml_file=os.path.join(settings.BASE_DIR,dura_config)
        with open(yaml_file,'rb') as f:
            if sys.version_info>(3,0):
                yaml_dict=yaml.load(f,Loader=yaml.FullLoader)
            else:
                yaml_dict=yaml.load(f)
        
        #使用单例模式
        return Dura(yaml_dict, settings.MONGODB_CONFIG)
    else:
        return None

dura=getDura()
