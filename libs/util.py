#coding:utf8
import os
import re
import uuid
import logging
import hashlib
import configparser


#使用setting.py中的log配置
MYLOGGER = logging.getLogger('solve.core.views')
MYLOGERROR = logging.getLogger('django.request')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

def plain_dict(data):
    for k in data:
        #将dict格式转成扁平的dict 即值只为str格式
        if isinstance(data[k],list):
            # 对list值进行格式化转换
            data[k]=" ".join(data[k])

    return data


def getcp(config_file=None):
    cp = configparser.ConfigParser()
    if not config_file:
        config_file=os.path.join(BASE_DIR,'deploy.conf')
    cp.read(config_file)
    return cp





