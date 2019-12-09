#coding:utf8
import re
import uuid
import logging
import hashlib
import configparser


#使用setting.py中的log配置
MYLOGGER = logging.getLogger('solve.core.views')
MYLOGERROR = logging.getLogger('django.request')

def my_md5(string):
    h = hashlib.md5()
    h.update(string.encode('utf8'))
    return h.hexdigest()

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

def getcp():
    cp = configparser.ConfigParser()
    cp.read('deploy.conf')
    return cp





