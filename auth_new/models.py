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
        index_together=('date_generate',)


class CASProxyToken(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.CharField(max_length=200,unique=True)
    token = models.CharField(max_length=300,null=True)

    class Meta:
        pass