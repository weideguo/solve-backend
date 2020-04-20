#coding:utf8
from auth_new import baseview
from libs.wrapper import error_capture

from rest_framework.response import Response
from django.http import HttpResponse

#class Test(baseview.AnyLogin):
class Test(baseview.BaseView):
    '''
    测试
    '''
    #@error_capture 
    def get(self, request, args = None):
        r={'a':'aaa'}
        """
        res=Response(r)
        res['Content-Type']='text/plain'    #在此不生效
        return res
        """

        
        import json
        r=json.dumps(r)
        #return HttpResponse(r,headers=headers)
        res=HttpResponse(r)
        res['Content-Type']='application/json'
        return res
        
