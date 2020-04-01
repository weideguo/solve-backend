#coding:utf8
import os
import re
import sys
import time
import json
import requests
from traceback import format_exc

from rest_framework.response import Response
from django.http import FileResponse

from auth_new import baseview
from libs import util
from conf import config
from libs.util import MYLOGGER,MYLOGERROR
from libs.wrapper import error_capture,file_root,playbook_root

solve_host="192.168.253.128"
solve_port=9000

#curl  "http://127.0.0.1:8000/api/v1/file/?path=./" -F "file=@/root/xxx.sh"
#real_url='http://127.0.0.1:9000/api/v1/file/?path=/tmp/a/b/c'
#file = {'file': open("/home/weideguo/get-pip.py", 'rb')}
#response = requests.post(real_url,headers=headers, files=files).text

def result_parse(res,msg1,msg2):
    r=None
    try:
        r_text=res.text
        r=json.loads(r_text)
        if "status" in r and r["status"]>0:
            r['msg']=util.safe_decode(msg1)
        else:
            MYLOGERROR.error(r_text)
            r=None
    except:
        MYLOGERROR.error(format_exc())
    if not r:
        r={'status':-1,'msg':util.safe_decode(msg2)}
    return r


class Test(baseview.AnyLogin):
    '''
    #实现对核心后端文件处理接口的转发
    中文路径 文件名支持 export LC_ALL=en_US.UTF-8
    '''
    base_url='http://%s:%s/file/' % (solve_host,solve_port)

    @error_capture
    def post(self, request, args = None):
        fr=request.FILES.get('file',None)      #curl "$url" -F "file=@/root/x.txt"  
        path=request.GET['path']   
        path=os.path.join(file_root,'./'+path)
        
        #help(fr)
        file = {'file': fr}
        url=self.base_url+"?path="+path
        r = requests.post(url, files=file)
        
        r=result_parse(r,'上传成功','上传出现错误，请查看日志')

        return Response(r)

    @error_capture
    def get(self, request, args = None):

        self.base_url=self.base_url+args
        if args == 'content':
            filename = request.GET['file']
            #是否是相对路径
            filename = os.path.join(playbook_root,filename)
            
            url=self.base_url+"?file="+filename
            r = requests.get(url)
            r=result_parse(r,'读取成功','读取失败，请查看日志')
            return Response(r)
                
        if args == 'download':
            filename = request.GET['file']
            name=os.path.basename(filename)
            filename = os.path.join(file_root,'./'+filename)

            #attachment下载文件, inline 和 attachment inline 在浏览器中显示
            showtype = ['attachment','inline', 'attachment inline'][0]

            url=self.base_url+"?file="+filename
            r = requests.get(url)
            try:
                response=FileResponse(r.content)
                response['Content-Type']='application/octet-stream'
                response['Content-Disposition']='%s;filename=%s' % (showtype, name.encode('utf8'))   
                #print("xxxxx")
                return response
            except:
                print(r.text)
                r=result_parse(r,'下载成功','下载失败，请查看日志')
                return Response(r)
       

        if args == 'list':
            root_path = request.GET['path']
            root_path = os.path.join(file_root,'./'+root_path)
            
            url=self.base_url+"?path="+root_path
            r = requests.get(url)
            r=result_parse(r,'查看成功','查看失败，请查看日志')
            return Response(r)

        if args == 'create':
            create_path = request.GET['path']
            create_path = os.path.join(file_root,'./'+create_path)
            
            url=self.base_url+"?path="+create_path
            r = requests.get(url)
            r=result_parse(r,'创建成功','创建失败，请查看日志')
            return Response(r)



