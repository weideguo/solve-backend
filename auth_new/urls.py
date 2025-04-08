# -*- coding: utf-8 -*- 

from django.urls import re_path

from auth_new.views import UserInfo,LoginAuth,AuthCAS,LogoutCAS

# 使用"/"结尾可以避免后续扩展时要改前端的请求
urlpatterns = [
    re_path(r'^userinfo/(.*)', UserInfo.as_view(), name='userinfo'),         
    re_path(r'^login/', LoginAuth.as_view(), name='login'),               #普通账号密码的登陆
    re_path(r'^cas/(.*)', AuthCAS.as_view(), name='cas'),                 #casd登陆认证以及cas proxy的使用
    re_path(r'^logout/', LogoutCAS.as_view(), name='logout'),             #登出cas 
]
