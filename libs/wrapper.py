#coding:utf8
import re
from traceback import format_exc

from rest_framework.response import Response
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError

from libs import util
from libs.util import MYLOGGER,MYLOGERROR


def error_capture(func):
    def my_wrapper(*args, **kwargs):
        try:
            request=args[1]
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                from_host=str(request.META['HTTP_X_FORWARDED_FOR'])
            else:
                from_host=str(request.META['REMOTE_ADDR'])

            MYLOGGER.info("%s %s %s" % (str(request.user),from_host,str(request.META['PATH_INFO']) ))
            return func(*args, **kwargs)
        except MultiValueDictKeyError as e:
            MYLOGERROR.error(format_exc())
            return HttpResponse(status=400)
        except Exception as e:
            MYLOGERROR.error(format_exc())
            return HttpResponse(status=500)
        
    return my_wrapper


class HashCURD():
    '''
    对hash类型的增删改查
    '''
    @staticmethod
    def get(redis_client,request, args = None):

        if args=='get':
            filter = request.GET['filter']
            page = int(request.GET.get('page',1))
            pagesize = int(request.GET.get('pagesize',16))
         
            filter=filter
            
            new_target_list = []
            
            target_list=redis_client.keys(filter)
            
            for t in target_list:
                if not re.match('^\S{32}$',t.split('_')[-1]):
                    b=redis_client.hgetall(t)
                    b.update({'name':t})
                    new_target_list.append(b)
            
            page_number=len(new_target_list)

            start = (page - 1) * pagesize
            end = page * pagesize
            data = new_target_list[start:end]
            
            return Response({'status':1, 'data': data, 'page': page_number})


        elif args=='del':
            target =  request.GET['target']
            redis_client.delete(target)
            return Response({'status':1})


        elif args=='info':
            '''
            简单的所有列表
            '''
            filter = request.GET['filter']        
            filter=filter
            target_list=redis_client.keys(filter)
            new_target_list = []
            for k in target_list:
                if not re.match('^\S{32}$',k.split('_')[-1]):
                    new_target_list.append(k)

            return Response({'status':1, 'data':new_target_list}) 

    @staticmethod
    def post(redis_client, request, args = None):
        try:
            info = request.data.dict()
        except:
            info = request.data            
        target = info.pop('name')
        
        target_o = info.pop('name_o','')
        if target_o:
            #修改
            if not redis_client.keys(target_o):
                return  Response({'status':-3,'msg':safe_decode('修改的对象不存在，请刷新后再试!')})
            elif target != target_o and redis_client.keys(target):
                return  Response({'status':-2,'msg':safe_decode('对象名已经存在，不能修改为此!')})
            else:
                redis_client.delete(target_o)
                redis_client.hmset(target,info)
                return  Response({'status':2,'msg':safe_decode('修改成功')})
        else:
            #增加
            if redis_client.keys(target):
                return  Response({'status':-1,'msg':safe_decode('添加的信息已经存在，不能再插入!')})            
            elif info:
                redis_client.hmset(target,info)    
                return  Response({'status':1,'msg':safe_decode('添加成功!')})
            else:
                return  Response({'status':-2,'msg':safe_decode('添加信息至少存在一个属性!')})



#使用cas proxy连接其他app时增加的函数

def set_gpt(pgtIou,service=None,pgtId=None):
    # 将获取的信息存储到数据库
    # pgtIou 主键
    # replace into cas_proxy_pgt values(pgtIou,service,pgtId)
    print(pgtIou,service,pgtId)

def get_token(service):
    # select token from cas_proxy_token where service='service'
    print(service)

def get_pgtId(service):
    # select pgtId from cas_proxy_pgt where service='service'
    print(service)


def set_token(service,token):
    # replace into cas_proxy_token(service,token) values('service','token')
    pass



def get_service_token(targetService):
    """
    获取请求service的jwt
    每次对其他app的接口发起请求前调用
    """
    token=get_token(targetService)            #token 可以复用 从数据库中获取
    if not token:
        pgtId=get_pgtId(targetService)        #pgtId 可以复用 从数据库中获取
        if pgtId:
            r=requests.get("%s/cas/proxy?pgt=%s&targetService=%s" %(cas_url,pgtId,targetService))
            x,y,msg=util.cas_info_parser(r.text)     #解析xml
            if ('proxyTicket' in msg) and isinstance(msg,dict):
                proxyTicket=msg['proxyTicket']

                # 请求其他服务的接口获取token
                service_proxyValidate_url="%s/api/v1/cas/proxyValidate" % targetService
                r=requests.get("%s?service=%s&ticket=%s" % (service_proxyValidate_url,targetService,proxyTicket))
                if 'token' in r.text:
                    token=r.text['token']
                    set_token(targetService,token)
                    msg=''
                else:
                    token=''
                    msg=r.text['msg']
                
            else:
                return '',msg
        else:
            return '','you should login again'
    
    return token,msg


