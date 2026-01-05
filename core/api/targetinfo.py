# -*- coding: utf-8 -*- 
import re
import redis
import json
import time
import uuid
from rest_framework.response import Response
from redis.exceptions import ResponseError
from django.utils.translation import gettext as _

from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import HashCRUD
from libs.redis_pool import redis_single


class Target(baseview.BaseView):
    '''
    执行对象的增删改查 
    '''    
    def get(self, request, args = None):
        redis_config_client = redis_single['redis_config']
        if args=='tree':
            '''
            获取树状结构
            '''
            data=[]
            target_name = request.GET['name']
            target_info=redis_config_client.hgetall(target_name)
            for k in target_info:
                i={}
                i['title']=k
                i['value']=target_info[k]
                try:
                    if redis_config_client.hgetall(target_info[k]):
                        #值为其他key的名字，则说明存在子节点，在此设置占位符
                        i['children']=[{}]
                except ResponseError:
                    #可能出现值为其他key的名字，但key不为hash类型，则将key当成普通字符串对待
                    pass

                data.append(i)

            return Response({'status':1,'data':data})
        if args=='detail':
            '''
            获取详细信息
            '''
            data = {}
            target_name = request.GET['name']
            target_field = request.GET.get('field','')
            
            target_info = redis_config_client.hgetall(target_name)

            if not target_info:
                return Response({'status':-1, 'data':'', 'msg': util.safe_decode(_('target not exist')) })
            if  target_field == '':
                return Response({'status':1,'data':target_info})
            
            next_target_name = ''
            # field字段可以为多层次的比如 const.host
            sub_key = ''
            for k in target_field.split('.'):
                sub_key = sub_key+'.'+k
                next_target_name = target_info.get(k)

                # if not next_target_name:   # 不能如此判断，可能为0、''
                if next_target_name == None:
                    #return Response({'status':-1, 'data':'', 'msg':'在对象%s获取字段%s信息失败' % (target_name,sub_key[1:]) })
                    return Response({'status':-1, 'data':'', 'msg': 
                                        util.safe_decode(
                                            _('get info of target [%(target_name)s] field [%(field)s] failed') 
                                            % {'target_name':target_name, 'field':sub_key[1:]} 
                                        ) 
                                    })

                target_info = redis_config_client.hgetall(next_target_name)
                
                if not target_info and sub_key[1:] == target_field:
                    # 对于最后一级的获取，可以只返回对象名
                    return Response({'status':2,'data':next_target_name})
            
            # 对于一般情况，需要返回最后一级的对象信息
            return Response({'status':1,'data':target_info})
        else:
            #其他的 get del info 操作
            return HashCRUD.get(redis_config_client, request, args, filter_tmp=config.spliter)

    def post(self, request, args = None):
        redis_config_client = redis_single['redis_config']
        return HashCRUD.post(redis_config_client,request, args)


class Host(baseview.BaseView):
    '''
    主机
    '''
    def get(self, request, args = None):
        redis_send_client = redis_single['redis_send']
        redis_log_client = redis_single['redis_log']
        redis_config_client = redis_single['redis_config']

        def get_online():
            online_host = redis_send_client.keys(config.prefix_heart_beat+'*')    
            real_online_host = []
            current_timestamp = time.time()
            for h in online_host:
                timestamp_gap=current_timestamp-float(redis_send_client.get(h))
                #在此以心跳间隔超过判断为断开
                if timestamp_gap < config.host_check_success_time:
                    is_conn=1
                else:
                    is_conn=0
                real_online_host.append({'host':h.split(config.prefix_heart_beat)[1],'timestamp_gap':timestamp_gap,'is_conn':is_conn})
            return real_online_host    

        if args=='online': 
            return Response({'status':1,'data':get_online()})
    

        elif args=='onlinedetail':
            real_online_list=[]
            for online in get_online():
                a={}
                a['name']=config.prefix_realhost+online['host']
                a['is_conn']=online['is_conn']
                real_online_info=redis_config_client.hgetall(a['name'])
                real_online_info.update(a)
                real_online_list.append(real_online_info)

            page_number=len(real_online_list)
            return Response({'status':1, 'data': real_online_list,'page': page_number})


        elif args=='kill':
            ip = request.GET['ip']
            redis_send_client.rpush(config.key_conn_control,config.pre_close+ip)
            
            kill_counter=0
            while redis_send_client.get(config.prefix_heart_beat+ip) and kill_counter<100:
                time.sleep(0.1)
                kill_counter=kill_counter+1       
            
            if kill_counter<100:
                deletelist = redis_send_client.keys('*'+ip+'*')
                for d in deletelist:
                    redis_send_client.delete(d)
                return  Response({'status':1, 'msg':util.safe_decode(_('close success')), 'delete_list':deletelist}) 
            else:
                return  Response({'status':-1, 'msg':util.safe_decode(_('close failed'))})

        
        elif args=='conn': 
            ip = request.GET['ip']
            conn_uuid=uuid.uuid1().hex
            redis_send_client.rpush(config.key_conn_control,ip+config.spliter+conn_uuid)
            
            conn_counter=0        
            while not redis_send_client.get(config.prefix_heart_beat+ip) and conn_counter<100 and (not redis_log_client.hget(conn_uuid,'exit_code')):
                time.sleep(0.1)
                conn_counter=conn_counter+1

            exit_code=redis_log_client.hget(conn_uuid,'exit_code')
            if exit_code=='0':
                return  Response({'status':1, 'msg':util.safe_decode(_('connect success'))})
            elif exit_code:
                return  Response({'status':-1, 'msg': util.safe_decode(exit_code)})
            elif conn_counter<100:
                return  Response({'status':1, 'msg':util.safe_decode(_('connect success'))})
            else:
                return  Response({'status':-2, 'msg':util.safe_decode(_('connect timeout'))})

