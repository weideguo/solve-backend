#coding:utf8
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
from django.conf import settings

from core.models import Account
from core.serializers import UserINFO
from libs import baseview, util
from libs.wrapper import error_capture,set_gpt



jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class userinfo(baseview.BaseView):
    '''
    用户信息的增删改查    
      
    '''
    @error_capture
    def get(self, request, args=None):
        page = request.GET.get('page',1)
        pagesize = int(request.GET.get('pagesize',16))
        page_number = Account.objects.count()

        start = (int(page) - 1) * pagesize
        end = int(page) * pagesize

        info = Account.objects.all()[start:end]
        info = UserINFO(info, many=True).data 
        
        return Response({'status':1,'page': page_number, 'data': info})


    @error_capture
    def put(self, request, args=None):
        username = request.data['username']
        new_password = request.data['new']
        
        user = Account.objects.get(username__exact=username)
        user.set_password(new_password)
        user.save()

        return Response({'status':1,'data':util.safe_decode('%s 密码修改成功') % username})


    @error_capture
    def post(self, request, args=None):
        username = request.data['username']
        password = request.data['password']

        if Account.objects.filter(username=username):
            return Response({'status':-1,'msg':util.safe_decode('%s 用户名已经存在!') % username})
        else:
            user = Account.objects.create_user(
                username=username,
                password=password)
            user.save()
            return Response({'status':1,'msg':util.safe_decode('%s 用户注册成功!') % username})

    @error_capture
    def delete(self, request, args=None):
        username=args
        Account.objects.filter(username=username).delete()
        return Response({'status':1,'data':util.safe_decode('%s 用户删除成功!') % username})


class login_auth(baseview.AnyLogin):
    @error_capture
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
            return Response({'status':-1,'token': '','msg':util.safe_decode('密码错误')})
        else:
            return Response({'status':-2,'token': '','msg':util.safe_decode('账号不存在')})



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


class auth_cas(baseview.AnyLogin):
    """
    使用cas系统的登陆
    """
    @error_capture
    def get(self, request, args = None):

        cas_url=settings.CAS_URL
        if not cas_url:
            return Response({'status':-3,'msg':util.safe_decode('必须先在后端设置CAS的地址才能使用')})

        service=request.GET['service']

        if args == 'login':
            """
            返回重定向到cas的信息
            """
            cas_login_url='%s/login?service=%s' %(cas_url,service)

            #直接返回重定向信息让浏览器跳转到cas
            #return redirect(cas_login_url)

            #window.location = <url>    #js获取返回值后，使用这种方式跳转，不能使用ajax发起请求
            return Response({'status':1,'cas_login_url':cas_login_url})

        if args == 'validate' or args == 'serviceValidate' or args == 'proxyValidate':
            """
            验证后返回 jwt token给前端
            前后端分离不适合使用cookie/session验证模式
            
            validate         返回text
            serviceValidate  返回xml
                ticket  前端将从cas系统获取到的ticket
                service 前端请求cas时的service
                pgtUrl  可选，用于接受cas回调的接口，由此接口接收PGTID，必须是https
                        接受的请求如 
                            "GET 
                                ?pgtId=PGT-1575617661-dIjdNxjsTyPNUx0DIlq0ohHbPIaFrIah
                                &pgtIou=PGTIOU-1575617661-ZHwypOEaklsvDsszDVrPGDuWnCGHctDh"

            proxyValidate
                使用cas proxy的登陆验证，用于验证其他app的登陆状态
                ticket  其他app获取到的proxyTicket
                service 其他app获取proxyTicket指定的targetService，即这个服的url，必须使用https
            """
            ticket=request.GET['ticket']
            verify=request.GET.get('verify',True)
            pgtUrl=request.GET.get('pgtUrl')

            if pgtUrl:
                # 要调用其它连接相同cas的app的接口时使用
                r=requests.get("%s/%s?ticket=%s&service=%s&pgtUrl=%s" % (cas_url,args,ticket,service,pgtUrl), verify=verify) 
                flag, user, msg = util.cas_info_parser(r.text)
                pgtIou=msg.get('proxyGrantingTicket')
                set_gpt(pgtIou,service=service)

            else:
                r=requests.get("%s/%s?ticket=%s&service=%s" % (cas_url,args,ticket,service), verify=verify)    

                flag, user, msg = util.cas_info_parser(r.text)

            #通过则设置session
            if flag:
                # 前后端分离不适合使用cookie/session验证模式，使用jwt代替 
                token=get_cas_user_token(user)
                return Response({'status':1,'user':user,'token':token})
            else:
                return Response({'status':-1,'msg':msg})


class cas_proxy(baseview.AnyLogin):

    @error_capture
    def get(self, request, args = None):
        """
        在作为代理时(即该服务要访问其他app的接口)，用于接收cas的回调
        """
        pgtId=request.GET['pgtId']
        pgtIou=request.GET['pgtIou']
        set_gpt(pgtIou,pgtId=pgtId)

        return Response({'status':1})


class logout_cas(baseview.BaseView):
    """
    登出 将对应的session清除 需要验证是否已经登陆
    """
    
    @error_capture
    def get(self, request, args = None):
        cas_url=settings.CAS_URL
        #service="http://192.168.59.132:8080/#/about"      #从请求获取前端的信息
        service=request.GET['service']

        username=str(request.user)
        Account.objects.filter(username=username).delete()
        # 返回重定向信息让浏览器使用存储的cookie登出cas，cas清理自己的cookies，然后再由cas返回至自己的登陆页面
        #return redirect('%s/logout?service=%s' %(cas_url,service))
        
        #window.location = <url>    #js获取返回值后，使用这种方式跳转，不能使用ajax发起请求
        return Response({'status':1, 'user':username, 'cas_logout_url':'%s/logout?service=%s' % (cas_url,service)})



