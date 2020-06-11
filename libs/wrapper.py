#coding:utf8
import os
import re

from rest_framework.response import Response

from libs import util, redis_pool
from libs.util import MYLOGGER,MYLOGERROR,safe_decode

from dura import solve_dura


redis_send_client,redis_log_client,redis_tmp_client,redis_config_client,redis_job_client,redis_manage_client = redis_pool.redis_init()


#函数不会多次运行，多次调用只运行一次

cp=util.getcp()

def get_cas_url():
    cas_url=""
    if cp.has_section("cas") and cp.has_option("cas","url"):
        cas_url=cp.get("cas","url")
    return cas_url

cas_url=get_cas_url()

def get_file_root():
    try:
        file_root=cp.get('common','file_root')
    except:
        file_root='/tmp/solve'
    
    if not os.path.isdir(file_root):
        os.makedirs(file_root)
    return file_root

def get_playbook_temp():
    try:
        base_dir=cp.get('common','playbook_temp')
    except:
        try:
            base_dir=cp.get('common','file_root')
        except:
            base_dir='/temp/'

    temp_dir=os.path.join(base_dir,'playbook/temp/')
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)

    return temp_dir

def get_playbook_root():
    #优先从配置文件deploy.conf获取，获取失败则从redis获取(solve后端在启动时设置对应参数)
    try:
        playbook_root=cp.get('common','playbook_root')
    except:
        playbook_root=""

    if not playbook_root:
        playbook_root=os.path.join(redis_send_client.hget("__solve__","base_dir"),"playbook")

    return playbook_root

def get_params(name,section='common',redis_key='__solve__'):
    #优先从配置文件deploy.conf获取，获取失败则从redis获取
    try:
        value=cp.get(section, name)
    except:
        value=""

    if not value:
        value=redis_send_client.hget(redis_key, name)

    if not value:
        value=""

    try:
        value=int(value)
    except:
        pass

    return value


file_root=get_file_root()
playbook_temp=get_playbook_temp()
playbook_root=get_playbook_root()

fileserver_bind=get_params('fileserver_bind')
fileserver_port=get_params('fileserver_port')


class HashCURD():
    '''
    对hash类型的增删改查
    '''
    @staticmethod
    def get(redis_client,request, args = None):

        if args=='get':
            '''
            获取列表及详细值
            '''
            filter = request.GET['filter']
            page = int(request.GET.get('page',1))
            pagesize = int(request.GET.get('pagesize',16))
            orderby = request.GET.get('orderby','')
            reverse = bool(int(request.GET.get('reverse',1))) 
            
            filter=filter
            
            new_target_list = []
            
            target_list=redis_client.keys(filter)
            
            for t in target_list:
                if not re.match('^\S{32}$',t.split('_')[-1]):
                    b=redis_client.hgetall(t)
                    b.update({'name':t})
                    new_target_list.append(b)
            
            page_number=len(new_target_list)

            if orderby:
                def sortitem(element):
                    sort_keyname=orderby
                    return element[sort_keyname] if sort_keyname in element else 0 
                
                new_target_list.sort(key=sortitem,reverse=reverse)   

            start = (page - 1) * pagesize
            end = page * pagesize
            data = new_target_list[start:end]
            
            return Response({'status':1, 'data': data, 'page': page_number})


        elif args=='del':
            '''
            删除
            '''
            target =  request.GET['target']
            redis_client.delete(target)
            if solve_dura:
                solve_dura.real_delete(target,redis_client)

            return Response({'status':1})


        elif args=='info':
            '''
            简单的匹配列表
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
        target = info.pop('name','')
        if not target:
            return  Response({'status':-4,'msg':safe_decode('name 字段必须存在')})

        target_o = info.pop('name_o','')
        if target_o:
            #修改
            if not redis_client.keys(target_o):
                return  Response({'status':-3,'msg':safe_decode('修改的对象不存在，请刷新后再试!')})
            elif target != target_o and redis_client.keys(target):
                return  Response({'status':-2,'msg':safe_decode('对象名已经存在，不能修改为此!')})
            else:
                redis_client.delete(target_o)
                if solve_dura:
                    solve_dura.real_delete(target_o,redis_client)

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






