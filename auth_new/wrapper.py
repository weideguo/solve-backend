# -*- coding: utf-8 -*- 
import json
import base64
import time
import requests
#import importlib

from django.conf import settings
from django.db import transaction

from . import util
from .models import CASProxyPgt,CASProxyToken


try:
    cas_url_name=settings.CAS_URL
except:
    cas_url_name=''

if cas_url_name:
    cas_url=util.get_obj(cas_url_name)
else:
    cas_url=''
        

try:
    translate_name=settings.TRANSLATE
    translate=util.get_obj(translate_name)
except:
    def translate(string,request=None):
        return string

#cas_url=getattr(settings,'CAS_URL','')
#
#translate=getattr(settings,'TRANSLATE','')
#if not translate:
#    def translate(string,request=None):
#        return string

#使用cas proxy连接其他app时增加的函数

def check_token(token):
    '''
    检查token是否已经过期
    '''
    if token:
        try:
            jwt_str =token.split('.')[1]+'=='     
            exp_time=json.loads(base64.b64decode(jwt_str).decode('utf8'))['exp']
            if exp_time-time.time() > 0:
                return token,''
            else:
                return '','token has expired'
        except:
            #出现解析错误，则不立即重新获取
            return token,'something wrong when parse token'
    else:
        return '',''


def get_service_token(service_proxyValidate,targetService=None,verify=True):
    '''
    如果需要调用其它app的接口，引用这个函数获取jwt即可
    每次对其他app的接口发起请求前调用
    service_proxyValidate     # 其他app的proxyValidate验证接口    
    targetService             # 需要为允许使用cas的service 可以为任意路径
    '''
    if not targetService:
        targetService='/'.join(service_proxyValidate.split('/')[:3]) 

    token_raw=CASProxyToken.objects.filter(service=targetService).values('token').first()
    if token_raw:
        token=token_raw.get('token')       #token 可以复用 从数据库中获取
    else:
        token=''

    token,msg=check_token(token)
    if not token:
        pgtId_raw=CASProxyPgt.objects.values('pgtId').order_by('-date_generate').first()
        if pgtId_raw:
            pgtId=pgtId_raw.get('pgtId')        #pgtId 可以复用 从数据库中获取
        else:
            pgtId=''

        if pgtId:
            r=requests.get('%s/proxy?pgt=%s&targetService=%s' %(cas_url,pgtId,targetService),verify=verify)
            x,y,msg=util.cas_info_parser(r.text,'proxySuccess')     #解析xml
            if ('proxyTicket' in msg) and isinstance(msg,dict):
                proxyTicket=msg['proxyTicket']

                # 请求其他服务的接口获取token
                # service_proxyValidate_url='%s/api/v1/cas/proxyValidate' % targetService
                r_token=requests.get('%s?service=%s&ticket=%s' % (service_proxyValidate,targetService,proxyTicket),verify=verify).text
                r_token=json.loads(r_token)
                if 'token' in r_token:
                    token=r_token['token']
                    with transaction.atomic():
                        CASProxyToken.objects.filter(service=targetService).delete()
                        CASProxyToken.objects.create(service=targetService,token=token)
                    msg=''
                else:
                    token=''
                    msg=r_token['msg']
                
            else:
                return '',msg
        else:
            return '','you should login again'
    
    return token,msg



