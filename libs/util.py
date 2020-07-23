# -*- coding: utf-8 -*- 
import os
import re
import uuid
import json
import logging
import hashlib
import configparser
import importlib


#使用setting.py中的log配置
MYLOGGER = logging.getLogger('solve.core.views')
MYLOGERROR = logging.getLogger('django.request')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def my_md5(string):
    h = hashlib.md5()
    h.update(string.encode('utf8'))
    return h.hexdigest()


def translate(string,request=None):
    '''
    翻译
    由前端请求的http头Accept-Language指定后端返回的语言
    默认使用zh_cn/zh-CN
    '''
    if request:
        try:
            lang= request.META['HTTP_ACCEPT_LANGUAGE']
        except:
            lang=''

        if not lang:
            lang='zh_cn'
        #前端可能传入类型如 zh-CN
        lang=lang.split(',')[0].replace('-','_').lower()  
        try:
            lang=importlib.import_module('conf.lang.'+lang)
        except:
            lang=importlib.import_module('conf.lang.zh_cn')

        #翻译失败时返回原字段名
        return getattr(lang, string, string)
    else:
        return string


def safe_decode(string):
    '''
    由其他编码转换成unicode
    '''
    try:
        #字符以utf8存储 转换成unicode
        return string.decode('utf8')
    except:
        #python3是字符都是以unicode存储 不能再转换
        return string

def plain_dict(data):
    for k in data:
        #将dict格式转成扁平的dict 即值只为str格式
        if isinstance(data[k],list):
            """
            # 对list值进行格式化转换 简单的以空格分隔存储 存在空格则出错
            data[k]='  '.join(data[k])
            """
            #转成字符串存储 允许存在空格
            data[k]=json.dumps(data[k],ensure_ascii=False).replace('[','').replace(']','').replace('\", \"','\" \"') 

    return data


def getcp(config_file=None):
    cp = configparser.ConfigParser()
    if not config_file:
        config_file=os.path.join(BASE_DIR,'deploy.conf')
    cp.read(config_file)
    return cp





