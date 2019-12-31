#coding:utf8

#from django.urls import include
from django.conf.urls import url,include
from rest_framework.urlpatterns import format_suffix_patterns

from core.api.order import Order
from core.api.execution import Session,Execution,ExecutionInfo
from core.api.targetinfo import Target,Host
from core.api.filemanage import File
from core.api.config import Config
from core.api.home import Home,Test
from core.api.dura import Dura

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^api/v1/home/(.*)', Home.as_view()),
    url(r'^api/v1/order/(.*)', Order.as_view()),
    url(r'^api/v1/target/(.*)', Target.as_view()),
    url(r'^api/v1/host/(.*)', Host.as_view()),
    url(r'^api/v1/executionInfo/(.*)', ExecutionInfo.as_view()),
    url(r'^api/v1/execution/(.*)', Execution.as_view()),
    url(r'^api/v1/session/(.*)', Session.as_view()),
    url(r'^api/v1/file/(.*)', File.as_view()),
    url(r'^api/v1/config/', Config.as_view()),
    url(r'^api/v1/dura/', Dura.as_view()),
    url(r'^api/v1/', include('auth_new.urls')),
    #url(r'^api/v1/test/(.*)', Test.as_view()),   #用于测试 正式部署请务必删除
]
urlpatterns = format_suffix_patterns(urlpatterns)
