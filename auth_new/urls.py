#coding:utf8

from django.conf.urls import url
#from rest_framework.urlpatterns import format_suffix_patterns

from auth_new.views import UserInfo,LoginAuth,AuthCAS,ProxyCAS,LogoutCAS

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^api/v1/userinfo/(.*)', UserInfo.as_view()),         
    url(r'^api/v1/api-token-auth/', LoginAuth.as_view()),      #普通账号密码的登陆
    url(r'^api/v1/cas/(.*)', AuthCAS.as_view()),               #casd登陆认证以及cas proxy的使用
    url(r'^api/v1/cas-proxy/(.*)',ProxyCAS.as_view()),         #cas proxy的回调
    url(r'^api/v1/logout/', LogoutCAS.as_view()),              #登出cas 
]
#urlpatterns = format_suffix_patterns(urlpatterns)
