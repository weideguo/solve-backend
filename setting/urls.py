# -*- coding: utf-8 -*- 

#from django.urls import include
from django.conf.urls import url,include
from rest_framework.urlpatterns import format_suffix_patterns

from core.api.order import Order
from core.api.execution import Session,Execution,ExecutionInfo,FastExecution,pauseRun
from core.api.targetinfo import Target,Host
from core.api.config import Config
from core.api.home import Home

from core.api.filemanage import File
#from core.api.fileproxy import FileProxy as File

from core.api.test import Test


# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^api/v1/home/(.*)', Home.as_view(), name='home'),
    url(r'^api/v1/order/(.*)', Order.as_view(), name='order'),
    url(r'^api/v1/target/(.*)', Target.as_view(), name='target'),
    url(r'^api/v1/host/(.*)', Host.as_view(), name='host'),
    url(r'^api/v1/executionInfo/(.*)', ExecutionInfo.as_view(), name='executionInfo'),
    url(r'^api/v1/execution/(.*)', Execution.as_view(), name='execution'),
    url(r'^api/v1/session/(.*)', Session.as_view(), name='session'),
    url(r'^api/v1/fast/(.*)', FastExecution.as_view(), name='fast'),
    url(r'^api/v1/pauseRun/(.*)', pauseRun.as_view(), name='pauseRun'),
    url(r'^api/v1/file/(.*)', File.as_view(), name='file'),
    url(r'^api/v1/config/', Config.as_view(), name='config'),
    url(r'^api/v1/', include(('auth_new.urls','auth'), namespace='auth') ),
    url(r'^api/v1/test/(.*)', Test.as_view()),   #用于测试 正式部署请务必删除
]
urlpatterns = format_suffix_patterns(urlpatterns)

#异常页面 没有明确设置则回复django的对应的默认页面
from libs.exception import page_not_found,inner_error
handler404 = page_not_found
handler500 = inner_error