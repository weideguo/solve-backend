# -*- coding: utf-8 -*- 

from django.conf.urls import url

from auth_new.views import UserInfo,LoginAuth,AuthCAS,LogoutCAS

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    url(r'^userinfo/(.*)', UserInfo.as_view(), name='userinfo'),         
    url(r'^login/', LoginAuth.as_view(), name='login'),               #普通账号密码的登陆
    url(r'^cas/(.*)', AuthCAS.as_view(), name='cas'),                 #casd登陆认证以及cas proxy的使用
    url(r'^logout/', LogoutCAS.as_view(), name='logout'),             #登出cas 
]
