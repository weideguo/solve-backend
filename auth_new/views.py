# -*- coding: utf-8 -*- 
import re
import hashlib
import json
import time
import uuid
import datetime
import requests
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import authenticate
from django.shortcuts import redirect

from . import baseview,util
from .models import Account,CASProxyPgt
from .serializers import UserINFO
from .wrapper import cas_url,translate



jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserInfo(baseview.BaseView):
    '''
    用户信息的增删改查
    '''
    def get(self, request, args=None):
        page = request.GET.get('page',1)
        pagesize = int(request.GET.get('pagesize',16))
        page_number = Account.objects.count()

        start = (int(page) - 1) * pagesize
        end = int(page) * pagesize

        info = Account.objects.all()[start:end]
        info = UserINFO(info, many=True).data 
        
        return Response({'status':1,'page': page_number, 'data': info})


    def put(self, request, args=None):
        username = request.data['username']
        new_password = request.data['new']
        
        user = Account.objects.get(username__exact=username)
        user.set_password(new_password)
        user.save()

        return Response({'status':1,'data':util.safe_decode(username+' '+translate('change_password_success',request)) })


    def post(self, request, args=None):
        username = request.data['username']
        password = request.data['password']

        if Account.objects.filter(username=username):
            return Response({'status':-1,'msg':util.safe_decode(username+' '+translate('user_exist_already',request))})
        else:
            user = Account.objects.create_user(
                username=username,
                password=password)
            user.save()
            return Response({'status':1,'msg':util.safe_decode(username+' '+translate('user_register_success',request))})

    def delete(self, request, args=None):
        username=args
        Account.objects.filter(username=username).delete()
        return Response({'status':1,'data':util.safe_decode(username+' '+translate('user_delete_success',request))})


class LoginAuth(baseview.AnyLogin):

    def post(self, request, args = None):
        '''
        登录验证
        :return: jwt token
        '''
        user = request.data['username']
        password = request.data['password']
        permissions = authenticate(username=user, password=password)
        #print(permissions) 
        
        if permissions:
            token = jwt_encode_handler(jwt_payload_handler(permissions))
            #使用jwt验证时依旧会查询数据库进行校验 仅对于此情况 并不是jwt的标准
            #如果需要外部数据库的账号表 可以在查询后再同步到本地
            #x = {'username': user, 'exp': datetime.datetime.fromtimestamp(time.time()+30000)}
            #token = jwt_encode_handler(x)
            return Response({'status':1,'token': token})
        elif Account.objects.filter(username=user):
            return Response({'status':-1,'token': '','msg':util.safe_decode(translate('password_error',request))})
        else:
            return Response({'status':-2,'token': '','msg':util.safe_decode(translate('user_not_exist',request))})



################################################# CAS ####################################################################
#使用django-mama-cas搭建cas服务验证

def get_cas_user_token(user):
    #由cas用户名获取jwt
    #每一次验证创建一个临时账号，重新验证时旧账号即作废
    tmp_user=user+'_'+uuid.uuid1().hex  
    password=uuid.uuid1().hex
    #使用like删除已类似的账号实现剔除废弃的账号
    Account.objects.filter(username__startswith=user+'_').delete()
    session_user = Account.objects.create_user(
        username=tmp_user,
        password=password)
    session_user.save()
    permissions = authenticate(username=tmp_user, password=password)
    token = jwt_encode_handler(jwt_payload_handler(permissions))
    return token


class AuthCAS(baseview.AnyLogin):
    '''
    使用cas系统的登陆
    '''
    def get(self, request, args = None):
        if not cas_url:
            return Response({'status':-3,'msg':util.safe_decode(translate('set_cas_before_used',request))})

        if args == 'login':
            '''
            返回重定向到cas的信息
            '''
            service=request.GET['service']
            cas_login_url='%s/login?service=%s' %(cas_url,service)

            #直接返回重定向信息让浏览器跳转到cas
            #return redirect(cas_login_url)

            #window.location = <url>    #js获取返回值后，使用这种方式跳转，不能使用ajax发起请求
            return Response({'status':1,'cas_login_url':cas_login_url})

        if args == 'validate' or args == 'serviceValidate' or args == 'proxyValidate':
            '''
            验证后返回 jwt token给前端
            前后端分离不适合使用cookie/session验证模式
            
            validate         返回text
            serviceValidate  返回xml
                ticket  前端将从cas系统获取到的ticket
                service 前端请求cas时的service
                pgtUrl  可选，用于接受cas回调的接口，由此接口接收PGTID，必须是https
                        接受的请求如 
                            'GET 
                                ?pgtId=PGT-1575617661-dIjdNxjsTyPNUx0DIlq0ohHbPIaFrIah
                                &pgtIou=PGTIOU-1575617661-ZHwypOEaklsvDsszDVrPGDuWnCGHctDh'

            proxyValidate
                使用cas proxy的登陆验证，用于验证其他app的登陆状态
                ticket  其他app获取到的proxyTicket
                service 其他app获取proxyTicket指定的targetService，必须使用https
            '''
            ticket=request.GET['ticket']
            service=request.GET['service']
            verify=request.GET.get('verify',True)
            pgtUrl=request.GET.get('pgtUrl')

            if pgtUrl:
                # 要调用其它连接相同cas的app的接口时使用
                url='%s/%s?ticket=%s&service=%s&pgtUrl=%s' % (cas_url,args,ticket,service,pgtUrl)
            else:
                url='%s/%s?ticket=%s&service=%s' % (cas_url,args,ticket,service)
            
            url=url.replace('#','%23')
            r=requests.get(url, verify=verify)    
            
            flag, user, msg = util.cas_info_parser(r.text,'authenticationSuccess')

            #通过则设置session
            if flag:
                # 前后端分离不适合使用cookie/session验证模式，使用jwt代替 
                token=get_cas_user_token(user)
                return Response({'status':1,'user':user,'token':token,'msg':msg})
            else:
                return Response({'status':-1,'msg':msg})

        if args == 'callback':
            '''
            在作为代理时(即该服务要访问其他app的接口)，用于接收cas的回调
            serviceValidate接口被请求时pgtUrl参数传入该接口作为回调
            获取参数存入数据库，需要为https
            '''
            #print(request.GET)
            pgtId=request.GET.get('pgtId')
            pgtIou=request.GET.get('pgtIou')

            if pgtId and pgtIou:
                CASProxyPgt.objects.create(pgtIou=pgtIou,pgtId=pgtId)
                return Response({'status':1})
            else:
                return Response({'status':-1})


class LogoutCAS(baseview.BaseView):
    '''
    登出 将对应的session清除 需要验证是否已经登陆
    '''
    
    def get(self, request, args = None):
        #service='http://192.168.59.132:8080/#/about'      #从请求获取前端的信息
        service=request.GET['service']

        username=str(request.user)
        Account.objects.filter(username=username).delete()
        # 返回重定向信息让浏览器使用存储的cookie登出cas，cas清理自己的cookies，然后再由cas返回至自己的登陆页面
        #return redirect('%s/logout?service=%s' %(cas_url,service))
        
        #window.location = <url>    #js获取返回值后，使用这种方式跳转，不能使用ajax发起请求
        if cas_url:
            return Response({'status':1, 'user':username, 'cas_logout_url':'%s/logout?service=%s' % (cas_url,service)})
        else:
            return Response({'status':1, 'user':username})



class TestProxy(baseview.BaseView):
    '''
    测试作为代理获取其他app的token
    即登陆该app之后，要访问其他app的接口，双方使用同一个cas且设置代理，则可以使用当前登陆的账号信息（不是通过保存账号密码）直接连接其他app，而不需要再次登陆
    要求登陆该app时serviceValidate接口附加参数pgtUrl
    '''
    def get(self, request, args = None):
        from auth_new.wrapper import get_service_token
        #https://192.168.59.132:9000/api/v1/cas/proxyValidate  需要访问的其他app的proxyValidate接口，不是该app的接口
        service_proxyValidate='https://192.168.59.132:9000/api/v1/cas/proxyValidate'
        token,msg=get_service_token(service_proxyValidate,verify=False)
        # verify是否验证https的证书
        # targetService 默认为 service_proxyValidate 的根路径
        #token,msg=get_service_token(service_proxyValidate,targetService=targetService,verify=0)
        return Response(str({'token':token,'msg':msg}))
