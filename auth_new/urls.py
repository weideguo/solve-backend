#coding:utf8

from django.conf.urls import url

from auth_new.views import UserInfo,LoginAuth,AuthCAS,LogoutCAS

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^userinfo/(.*)', UserInfo.as_view()),         
    url(r'^login/', LoginAuth.as_view()),               #普通账号密码的登陆
    url(r'^cas/(.*)', AuthCAS.as_view()),               #casd登陆认证以及cas proxy的使用
    url(r'^logout/', LogoutCAS.as_view()),              #登出cas 
]
