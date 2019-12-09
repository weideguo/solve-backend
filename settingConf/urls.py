#coding:utf8

from django.urls import include
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

#from core.api.user import userinfo,login_auth,auth_cas,logout_cas
from core.api.myorder import myorder,order
from core.api.execution import mysession,myexecution,executioninfo
from core.api.targetinfo import targetinfo,host
from core.api.home import home,test
from core.api.filemanage import filemanage
from core.api.myconfig import myconfig

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^api/v1/home/(.*)', home.as_view()),
    url(r'^api/v1/myorder/', myorder.as_view()),
    url(r'^api/v1/order/(.*)', order.as_view()),
    url(r'^api/v1/targetinfo/(.*)', targetinfo.as_view()),
    url(r'^api/v1/executioninfo/(.*)', executioninfo.as_view()),
    url(r'^api/v1/hostmanage/(.*)', host.as_view()),
    url(r'^api/v1/myexecution/(.*)', myexecution.as_view()),
    url(r'^api/v1/mysession/', mysession.as_view()),
    url(r'^api/v1/file/(.*)', filemanage.as_view()),
    url(r'^api/v1/config/', myconfig.as_view()),
    url(r'^api/v1/test/(.*)', test.as_view()),   #用于测试 正式部署请务必删除
    url(r'', include('auth_new.urls')),
    #url(r'^api/v1/userinfo/(.*)', userinfo.as_view()),
    #url(r'^api/v1/api-token-auth/', login_auth.as_view()),
    #url(r'^api/v1/cas/(.*)', auth_cas.as_view()),    #测试使用cas
    #url(r'^api/v1/logout/', logout_cas.as_view()),    #测试登出cas 
]
urlpatterns = format_suffix_patterns(urlpatterns)
