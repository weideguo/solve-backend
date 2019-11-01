#coding:utf8
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    BasePermission
)

from rest_framework.views import APIView


class BaseView(APIView):
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


class AnyLogin(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request, args = None):
        pass

    def post(self, request, args = None):
        pass

    def put(self, request, args = None):
        pass

    def delete(self, request, args = None):
        pass
