# -*- coding: utf-8 -*- 
import os
import re
import sys
import time
import json
import requests
import tempfile
from traceback import format_exc

from rest_framework.response import Response
from django.http import FileResponse
from django.utils.encoding import escape_uri_path
from django.utils.translation import gettext as _

from auth_new import baseview
from libs import util
from conf import config
from libs.util import MYLOGGER,MYLOGERROR
from libs.wrapper import file_root,playbook_root,fileserver_bind,fileserver_port


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


class FileProxy(baseview.BaseView):
    '''
    #实现对核心后端文件处理接口的转发
    中文路径 文件名支持 export LC_ALL=en_US.UTF-8
    '''
    base_url='http://%s:%s/file/' % (fileserver_bind,fileserver_port)

    def post(self, request, args = None):
        fr=request.FILES.get('file',None)      #curl "$url" -F "file=@/root/x.txt"  
        path=request.GET['path']   
        if re.match('.*\.\..*',path):
            return Response({'status':-1,'file':path,'msg':util.safe_decode(_('should not change in path'))})

        path=os.path.join(file_root,'./'+path)
        
        file = {'file': fr}
        url=self.base_url+"?path="+path
        r = requests.post(url, files=file)
        
        r=result_parse(r,_('upload success'),_('upload failed tips'))

        return Response(r)

    def get(self, request, args = None):

        for path in [request.GET.get('file',''),request.GET.get('path','')]:
            if re.match('.*\.\..*',path):
                return Response({'status':-1,'path':path,'msg':util.safe_decode(_('should not change in path'))})

        self.base_url=self.base_url+args
        if args == 'content':
            filename = request.GET['file']

            #是否是相对路径
            filename = os.path.join(playbook_root,filename)
            
            url=self.base_url+"?file="+filename
            r = requests.get(url)
            r=result_parse(r,_('read success'),_('read failed tips'))
            return Response(r)
                
        if args == 'download':
            filename = request.GET['file']

            name=os.path.basename(filename)
            filename = os.path.join(file_root,'./'+filename)

            #attachment下载文件, inline 和 attachment inline 在浏览器中显示
            showtype = ['attachment','inline', 'attachment inline'][0]

            url=self.base_url+"?file="+filename
            r = requests.get(url)
            
            if r.status_code == 200:
                try:
                    # 使用临时文件流将字符串转成流
                    f=tempfile.NamedTemporaryFile()
                    f.write(r.content)
                    f.flush()
                    f.seek(0)
                    #f=open("/path_to_file/xxx")
                    response=FileResponse(f)     #不会处理失败
                    response['Content-Type']='application/octet-stream'
                    #response['Content-Disposition']='%s;filename=%s' % (showtype, name.encode('utf8'))  
                    response['Content-Disposition']='%s;filename=%s' % (showtype, escape_uri_path(name))  
                    return response
                except:
                    r=result_parse(r,_('download success'),_('parse result failed tips'))
                    return Response(r)
            else:
                r=result_parse(r,_('download success'),_('download failed tips'))
                return Response(r,status=404)
       

        if args == 'list':
            root_path = request.GET['path']

            root_path = os.path.join(file_root,'./'+root_path)
            
            url=self.base_url+"?path="+root_path
            r = requests.get(url)
            r=result_parse(r,_('list success'),_('list failed tips'))
            return Response(r)

        if args == 'create':
            create_path = request.GET['path']

            create_path = os.path.join(file_root,'./'+create_path)
            
            url=self.base_url+"?path="+create_path
            r = requests.get(url)
            r=result_parse(r,_('create success'),_('create failed tips'))
            return Response(r)
