#coding:utf8
from django.http import HttpResponse

def page_not_found(request,exception):
    return HttpResponse('Path Not Found',status=404)

def inner_error(request):
    return HttpResponse('Server Error',status=500)
