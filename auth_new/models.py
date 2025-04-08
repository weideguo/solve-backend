# -*- coding: utf-8 -*- 
from django.db import models
from django.contrib.auth.models import AbstractUser


class Account(AbstractUser):
    '''
    User table
    '''
    #group = models.CharField(max_length=40)                                             # 权限组 guest/admin
    #department = models.CharField(max_length=40)                                        # 部门
    #auth_group = models.CharField(max_length=100, null=True)                            # 细粒化权限组
    #real_name = models.CharField(max_length=100, null=True, default='请添加真实姓名')   # 真实姓名



class CASProxyPgt(models.Model):
    pgtIou = models.CharField(max_length=200, primary_key=True)
    pgtId = models.CharField(max_length=200,null=True)
    date_generate = models.DateTimeField(auto_now = True)

    class Meta:
        indexes = [
            models.Index(fields=['date_generate',]),
        ]


class CASProxyToken(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.CharField(max_length=200,unique=True)
    token = models.CharField(max_length=300,null=True)

    class Meta:
        pass
        

class PermanentToken(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=32,unique=True)                                           # 提供给外部调用api的token，32位
    username = models.CharField(max_length=150)                                                   # 对应account的username账号
    
    invoke_rule_ids = models.CharField(max_length=200, default='')                                # 请求限制规则id列表，“,”分隔，匹配一条规则即可以通过
    
    is_validate = models.IntegerField(default=1)                                                  # 是否生效，0则不生效，1则生效
    validate_date = models.DateTimeField(blank=True, null=True)                                   # 生效期限，为空则表示永久生效
    create_date = models.DateTimeField(auto_now = True)                                           # 创建时间
    max_invoke = models.IntegerField(default=999999)                                              # 成功调用次数上限
    
    invoke_count = models.IntegerField(default=0)                                                 # 全部调用的次数
    invoke_success_count = models.IntegerField(default=0)                                         # 成功调用的次数
    lastest_date = models.DateTimeField(auto_now = True)                                          # 上一次调用的时间
    lastest_success_date = models.DateTimeField(auto_now = True)                                  # 上一次成功调用的时间


class ApiInvokeRule(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=100, blank=True, null=True)                                 # 路径，使用正则 ["路径1","路径2"]
                                                                                                   # 规则为空则允许所有，规则非空，则需要至少匹配一条规则，空可以为null、"[]"、""
    source =  models.CharField(max_length=512, blank=True, null=True)                              # 发起请求的IP，使用正则 ["限制1","限制2"]
    method = models.CharField(max_length=50, blank=True, null=True)                                # 请求方法 ["GET","POST"]
    params = models.CharField(max_length=512, blank=True, null=True)                               # 请求参数，使用正则 ["限制1","限制2"]
    body = models.CharField(max_length=512, blank=True, null=True)                                 # 请求体，使用正则 ["限制1","限制2"]
    
    
    