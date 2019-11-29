#coding:utf8
import re
import hashlib
import json
import time
import datetime
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import authenticate
from django.shortcuts import redirect

from core.models import Account
from core.serializers import UserINFO
from libs import baseview, util
from libs.util import error_capture,safe_decode



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

        return Response({'status':1,'data':safe_decode('%s 密码修改成功') % username})


    @error_capture
    def post(self, request, args=None):
        username = request.data['username']
        password = request.data['password']

        if Account.objects.filter(username=username):
            return Response({'status':-1,'msg':safe_decode('%s 用户名已经存在!') % username})
        else:
            user = Account.objects.create_user(
                username=username,
                password=password)
            user.save()
            return Response({'status':1,'msg':safe_decode('%s 用户注册成功!') % username})

    @error_capture
    def delete(self, request, args=None):
        username=args
        Account.objects.filter(username=username).delete()
        return Response({'status':1,'data':safe_decode('%s 用户删除成功!') % username})


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
            return Response({'status':-1,'token': '','msg':safe_decode('密码错误')})
        else:
            return Response({'status':-2,'token': '','msg':safe_decode('账号不存在')})




class auth_cas(baseview.AnyLogin):
    """
    使用cas系统的登陆
    """
    @error_capture
    def get(self, request, args = None):

        cas_url="http://192.168.59.132:9095/cas"  #在后端配置
        my_url="http://192.168.59.132:8080/#/about"      #从请求获取前端的信息

        if args == 'login':
            """
            返回重定向到cas的信息
            """
            #直接返回重定向信息让浏览器跳转到cas
            return redirect('%s/login?service=%s' %(cas_url,my_url))

            #返回重定向信息让前端js处理
            #return Response({'status':1,'cas_url':cas_url+'/login'})

        if args == 'validate' or args == 'serviceValidate':
            """
            前端将从cas系统获取到ticket传到此，验证后返回
            前后端分离使用cookie/session js发的请求时自己拼接上cookie
            """
            ticket=request.GET.get('ticket')
            import requests
            r=requests.get("%s/%s?ticket=%s&service=%s" % (cas_url,args,ticket,my_url))    


            from xml.etree import ElementTree as ET
            try:
                root=ET.XML(r.text)
                # xml时的解析
                # <tag attrib>text<child/>...</tag>tail
                try:
                    auth_info={}
                    m = re.match('\{.*\}', root.tag)
                    xmlns=m.group(0) if m else ''
                    for a in root:
                        if a.tag.split(xmlns)[-1] == 'authenticationSuccess':
                            for u in a:
                                auth_info[u.tag.split(xmlns)[-1]] = u.text
                        else:
                            return Response({'status':-1,'msg':a.text,'attrib':a.attrib})

                    if 'user' in auth_info:
                        user=auth_info['user']
                        flag=True
                    else:
                        user=''
                        flag=False
                    msg=auth_info

                except:
                    return Response({'status':-2,'msg':r.text})

            except:
                # text时的解析
                try:
                    flag, user, x=r.text.split('\n')
                    flag=(flag.lower()=='yes')
                    msg=r.text
                except:
                    return Response({'status':-2,'msg':msg})


            #通过则设置session
            if flag:
                # session值任意设置一个，校验时只判断是否存在？
                request.session[user]=time.time()
                return Response({'status':1,'user':user})
            else:
                return Response({'status':-1,'msg':msg})


class logout_cas(baseview.SessionView):
    """
    登出 将对应的session清除 需要验证是否已经登陆
    """
    
    @error_capture
    def get(self, request, args = None):
        cas_url="http://192.168.59.132:9095/cas"         #在后端配置
        my_url="http://192.168.59.132:8080/#/about"      #从请求获取前端的信息

        # 必须浏览器提交才同时自动提交cookie 即<a>标签 
        # js提交则不能 需要自己拼接上 cookie
        user=request.session.keys()

        #request.session.delete(session_key)
        from django.shortcuts import HttpResponse
        return HttpResponse(str(user))
        #return Response({'status':1,'user':user,'cas_url':cas_url+'/logout'})
        # 返回重定向信息让浏览器使用存储的cookie登出cas，然后再由cas返回至自己的登陆页面
        #return redirect('%s/logout?service=%s' %(cas_url,my_url))

