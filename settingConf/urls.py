#coding:utf8
'''
url table
'''
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from core.api.user import userinfo,login_auth
from core.api.myorder import myorder,order
from core.api.execution import mysession,myexecution,executioninfo
from core.api.targetinfo import targetinfo,host
from core.api.home import home
from core.api.filemanage import filemanage
from core.api.myconfig import myconfig

urlpatterns = [
    url(r'^api/v1/home/(.*)', home.as_view()),
    url(r'^api/v1/userinfo/(.*)', userinfo.as_view()),
    url(r'^api/v1/myorder', myorder.as_view()),
    url(r'^api/v1/order/(.*)', order.as_view()),
    url(r'^api/v1/targetinfo/(.*)', targetinfo.as_view()),
    url(r'^api/v1/executioninfo/(.*)', executioninfo.as_view()),
    url(r'^api/v1/hostmanage/(.*)', host.as_view()),
    url(r'^api/v1/myexecution/(.*)', myexecution.as_view()),
    url(r'^api/v1/mysession/', mysession.as_view()),
    url(r'^api/v1/file/(.*)', filemanage.as_view()),
    url(r'^api/v1/api-token-auth/', login_auth.as_view()),
    url(r'^api/v1/config', myconfig.as_view()),
]
urlpatterns = format_suffix_patterns(urlpatterns)
