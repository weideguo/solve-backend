# -*- coding: utf-8 -*- 
from rest_framework.response import Response

def super_privilege(msg):
    def _decorator(func):
        def __wrapper(self, request, args):
            if request.user.is_superuser:
                return func(self, request, args)
            else:
                return Response({'status':-1, 'msg':msg})
            
        return __wrapper
    return _decorator
