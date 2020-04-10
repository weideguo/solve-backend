#coding:utf8
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    BasePermission
)

from rest_framework.views import APIView


class BaseView(APIView):
    '''
    settings.py REST_FRAMEWORK 模块设置的验证方法
    '''
    permission_classes = (IsAuthenticated,)
    #permission_classes = ()
    #authentication_classes = ()

    def get(self, request, args = None):
        pass

    def post(self, request, args = None):
        pass

    def put(self, request, args = None):
        pass

    def delete(self, request, args = None):
        pass


class SuperUserpermissions(APIView):
    permission_classes = (IsAdminUser,)
    authentication_classes = ()

    def get(self, request, args = None):
        pass

    def post(self, request, args = None):
        pass

    def put(self, request, args = None):
        pass

    def delete(self, request, args = None):
        pass

from rest_framework.throttling import ScopedRateThrottle
class AnyLogin(APIView):
    permission_classes = ()
    authentication_classes = ()

    #settings.py REST_FRAMEWORK.DEFAULT_THROTTLE_RATES设置访问频率
    throttle_scope='anylogin'
    throttle_classes = [ScopedRateThrottle]

    def get(self, request, args = None):
        pass

    def post(self, request, args = None):
        pass

    def put(self, request, args = None):
        pass

    def delete(self, request, args = None):
        pass

