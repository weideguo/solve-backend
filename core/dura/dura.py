#coding:utf8
import os
import re
import sys
import time
import redis
import yaml
from threading import Thread
from traceback import format_exc

from django.conf import settings
from pymongo import MongoClient 

from libs import redis_pool

from libs.util import MYLOGGER,MYLOGERROR


class Dura():
    '''
    持久化操作
    '''

    def __init__(self, key_map_config, mongodb_config, redis_client_set, time_gap=60, \
                type_name='__type', primary_key='__pid', 
                list_name='list_value',set_name='set_value',str_name='str_value',zset_name='zset_value'):
        '''
        key_map_config   redis key与mongodb映射关系
        mongodb_config   mongodb的配置
        time_gap         redis同步到mongodb的时间间隔
        '''
        
        self.key_map_config = key_map_config

        self.type_name = type_name           #存放在mongodb时的记录key类型的字段
        self.primary_key = primary_key       #存放在mongodb时的记录key名字的字段，设置为主键或唯一键

        #hash 的数据不能存在字段 self.primary_key self.type_name '_id'
        self.list_name = list_name           #redis的key为list类型值存储在mongodb的字段
        self.set_name = set_name             #set类型的值存储在mongodb的字段
        self.str_name = str_name             #string类型的值存储在mongodb的字段
        self.zset_name = zset_name           #zset类型的值存储在mongodb的字段

        #pymongo内置连接池，可以自动处理网络波动问题，阻塞等待
        conn=MongoClient(host=mongodb_config['host'], port=mongodb_config['port'])
        self.db=conn[mongodb_config['db']]
        if ('user' in mongodb_config) and mongodb_config['user']:
            self.db.authenticate(mongodb_config['user'], mongodb_config['passwd']) 

        self.redis_client_set=redis_client_set
        self.time_gap = time_gap
        self.__backgroup()


    def __save(self):
        '''
        从redis保存数据到mongodb
        '''
        while True:
            for db_config in self.key_map_config['save']:
                pos=list(db_config.keys())[0]
                
                redis_client=self.redis_client_set[pos]

                #可能太大 使用scan代替
                for k in redis_client.keys():        
                    for key_config in db_config[pos]:
                        if re.match(key_config['key_pattern'], k):
                            collection_name = key_config['collection']
                            is_update = key_config.get('update',1)
                            try:
                                self.save(k, redis_client, collection_name, is_update)
                            except:
                                MYLOGERROR.error(format_exc())
                                MYLOGERROR.error('save key failed-------%s %s %s %s' % (k, str(redis_client), collection_name, is_update))

                            #print('save key ------- %s %s' % (k,str(redis_client)))
            #print('save key from redis to mongodb')
            MYLOGGER.info('save key from redis to mongodb done')
            time.sleep(self.time_gap)


    def save(self, key, redis_client, collection_name, is_update=1):
        '''
        redis中单个key的存储
        '''
        value = {}
        #根据pid判定在mongodb中是否存在
        exist_count = self.db[collection_name].find({self.primary_key: key}).count()
        key_type = redis_client.type(key)
        value[self.type_name] = key_type
        value[self.primary_key] = key
            
        if key_type == 'list':
            all_list = redis_client.lrange(key,0,redis_client.llen(key))
                        
            if exist_count and is_update==-1:
                #mongodb中记录存且key类型为只插入不存在的key
                #根据原有list的最后一个值 截取从redis获取的list 只插入新增加的
                #redis中list不能只删除最后一个！！！否则这里会出错
                #获取对应记录中list的最后一个值 返回list格式
                key_list=self.db[collection_name].find({self.primary_key: key},{ self.list_name: { '$slice': -1 }})[0].get(self.list_name, [])
                
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
                #print('save key -------%s %s  %s' % (new_list, key, str(i)))
                self.db[collection_name].update({self.primary_key: key},{'$push':{self.list_name: {'$each': new_list}}})
                return key,'update reduce'
            elif exist_count and is_update==0:
                #mongodb中记录存在或者key类型为不更新
                return key, None
            elif exist_count and is_update==1:
                #mongodb中记录存在且key类型为全量替换
                value[self.list_name]=all_list
                self.db[collection_name].update({self.primary_key: key}, value)
                return key, 'update'
            else:
                #mongodb中记录不存在
                value[self.list_name]=all_list
                self.db[collection_name].insert(value)
                return key, 'insert'
        else:
            if key_type == 'hash':
                value = redis_client.hgetall(key)
                value[self.type_name] = key_type
                value[self.primary_key] = key
            elif key_type == 'set':
                value[self.set_name]=list(redis_client.smembers(key))
            elif key_type == 'string':
                value[self.str_name]=redis_client.get(key)
            elif key_type == 'zset':
                _value=[]
                cursor,v =redis_client.zscan(key)
                _value += v
                while cursor:
                    cursor,v =redis_client.zscan(key,cursor)
                    _value += v
                value[self.zset_name] = _value
            else:
                return None,'type error'

            if exist_count and is_update:
                #在mongodb中存在且key类型为更新
                self.db[collection_name].update({self.primary_key: key}, value)
                return key,'update'
            elif not exist_count:
                #在mongodb中不存在
                self.db[collection_name].insert(value)
                return key,'insert'
            else:
                #存在且key类型为不更新则跳过
                return key, None

                                
    def x__load(self):
        pass


    def __load(self):
        '''
        mongodb数据自动加载到redis
        只在初始化时进行一次
        '''
        for db_config in self.key_map_config['load']:
            pos=list(db_config.keys())[0]
            
            redis_client=self.redis_client_set[pos]

            for key_config in db_config[pos]:
                collection_name = key_config['collection']
                is_update = key_config.get('update',1)
                self.real_load(redis_client, collection_name, is_update=is_update)
                #print(redis_client, collection_name)
                MYLOGGER.info('load collection [ %s ] from mongodb to redis done' % collection_name)


    def get_collection_name(self, key, redis_client):
        '''
        由key名在save模块获取对应的mongodb collention信息
        '''
        pos=0
        for r in self.redis_client_set: 
            if str(r)==str(redis_client):
                break
            pos=pos+1       

        collection_name=None
        for db_config in self.key_map_config['save']:
            if list(db_config.keys())[0] == pos:
                for key_config in db_config[pos]:
                    if re.match(key_config['key_pattern'],key):
                        collection_name=key_config['collection']

        return collection_name


    def load(self, key, redis_client, is_update=1):
        '''
        单个key加载，对外提供接口
        使用save模块的配置
        '''
        collection_name=self.get_collection_name(key, redis_client)
        summary={}
        if collection_name:
            summary=self.real_load(redis_client, collection_name, {self.primary_key: key}, is_update)
            #print(redis_client, collection_name, {self.primary_key: key})
        return collection_name, {self.primary_key: key}, summary


    def real_load(self, redis_client, collection_name, find=None, is_update=1):
        '''
        实际从mongodb加载数据到redis
        '''
        summary={'update':0, 'skip': 0 ,'error': 0}
        for key_info in self.db[collection_name].find(find):

            type_name=key_info.pop(self.type_name, '')
            key_name=key_info.pop(self.primary_key, '')
            if key_name:
                key_exist=redis_client.exists(key_name)
                if is_update or (not key_exist):
                    #为更新或者不存在 则全部使用mongodb的数据替换
                    #hash 只替换mongodb存在的属性
                    #list set zset 先删除已有的key
                    key_info.pop('_id', '')
                    is_error=0
                    if (not type_name) or type_name=='hash':
                        redis_client.hmset(key_name, key_info)
                    elif type_name=='string':
                        redis_client.set(key_name, key_info[self.str_name])
                    else:
                        if type_name=='list': 
                            k=self.list_name 
                            if (k in key_info) and (isinstance(key_info[k],list)):
                                redis_client.delete(key_name)
                                redis_client.rpush(key_name, *key_info[k])
                            else:
                                is_error=1
                        elif type_name=='set':
                            k=self.set_name 
                            if (k in key_info) and (isinstance(key_info[k],list)):
                                redis_client.delete(key_name)
                                redis_client.sadd(key_name, *key_info[k])
                            else:
                                is_error=1
                        elif type_name=='zset':
                            k=self.zset_name 
                            if (k in key_info) and (isinstance(key_info[k],list)):
                                mapping={}
                                try:
                                    for i in key_info[k]:
                                        mapping[i[0]]=i[1]

                                    redis_client.delete(key_name)     
                                    redis_client.zadd(key_name, mapping)
                                except:
                                    is_error=1 
                            else:
                                is_error=1
                        else:
                            is_error=1

                    if is_error:
                        key_info[self.primary_key]=key_name
                        MYLOGERROR.error('key info error, %s at collection [ %s ] out of expect' % (str(key_info), collection_name))
                        summary['error'] += 1
                    else:
                        summary['update'] += 1
                else:
                    #key存在且为不更新 则跳过
                    summary['skip'] += 1
                
            else:
                MYLOGERROR.error('key info error, \'%s\' not in %s at collection [ %s ]' % (self.primary_key, str(key_info), collection_name))
                summary['error'] += 1

        return  summary


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
        redis_client_set=redis_pool.redis_init()

        yaml_file=os.path.join(settings.BASE_DIR,dura_config)
        with open(yaml_file,'rb') as f:
            if sys.version_info>(3,0):
                yaml_dict=yaml.load(f,Loader=yaml.FullLoader)
            else:
                yaml_dict=yaml.load(f)
        
        return Dura(yaml_dict, settings.MONGODB_CONFIG, redis_client_set)
    else:
        MYLOGGER.info('not durability for MONGODB_CONFIG [ %s ] in settings ' % str(MONGODB_CONFIG))
        return None

#使用单例模式
dura=getDura()
