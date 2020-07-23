# -*- coding: utf-8 -*- 
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    BasePermission
)

from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from django.http import HttpResponse

class DefaultView(object):
    '''
    没有覆盖这些函数时 默认对请求的响应
    '''
    def get(self, request, args = None):
        return HttpResponse('not implement this operation yet',status=400)

    def post(self, request, args = None):
        return HttpResponse('not implement this operation yet',status=400)

    def put(self, request, args = None):
        return HttpResponse('not implement this operation yet',status=400)

    def delete(self, request, args = None):
        return HttpResponse('not implement this operation yet',status=400)


class BaseView(DefaultView, APIView):
    '''
    settings.py REST_FRAMEWORK 模块设置的验证方法
    '''
    permission_classes = (IsAuthenticated,)
    #permission_classes = ()
    #authentication_classes = ()


class SuperUserpermissions(DefaultView, APIView):
    permission_classes = (IsAdminUser,)
    authentication_classes = ()


class AnyLogin(DefaultView, APIView):
    permission_classes = ()
    authentication_classes = ()

    #settings.py REST_FRAMEWORK.DEFAULT_THROTTLE_RATES设置访问频率
    throttle_scope='anylogin'
    throttle_classes = [ScopedRateThrottle]


class TestView(DefaultView, APIView):
    '''
    没有任何限制，用于测试
    '''
    permission_classes = ()
    authentication_classes = ()


