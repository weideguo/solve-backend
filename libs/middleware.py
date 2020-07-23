# -*- coding: utf-8 -*- 
from traceback import format_exc

from redis.exceptions import ConnectionError

from rest_framework.response import Response
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.deprecation import MiddlewareMixin

from libs.util import MYLOGGER,MYLOGERROR


class MyMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, ConnectionError):
            return HttpResponse('redis connection failed',status=500)
        elif isinstance(exception, MultiValueDictKeyError):
            MYLOGERROR.error(format_exc())
            return HttpResponse('paramster error',status=400)
        else:
            MYLOGERROR.error(format_exc())
            return HttpResponse('unknow error, please check server log',status=500)

    #def process_view(self, request, view_func, view_args, view_kwargs):
    def process_response(self, request, response):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            from_host=str(request.META['HTTP_X_FORWARDED_FOR'])
        else:
            from_host=str(request.META['REMOTE_ADDR'])

        #路径找不到时user不存在
        if not hasattr(request,'user'):
            request.user='NullUser'
            
        MYLOGGER.info("%s %s %s" % (str(request.user),from_host,str(request.META['PATH_INFO']) ))
        
        return response


