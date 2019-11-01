#coding:utf8
import hashlib
import json
import time
import datetime
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import authenticate

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

