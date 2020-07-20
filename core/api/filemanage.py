#coding:utf8
import os
import re
import sys
import time
from rest_framework.response import Response
from django.http import FileResponse

from auth_new import baseview
from libs import util
from conf import config

from libs.wrapper import file_root,playbook_root
from libs.util import translate

class File(baseview.BaseView):
    '''
    关于文件的操作
    中文路径 文件名支持 export LC_ALL=en_US.UTF-8
    '''
    def post(self, request, args = None):
        fr=request.FILES.get('file',None)      #curl "$url" -F "file=@/root/x.txt"  
        path=request.GET['path'] 
        if re.match('.*\.\..*',path):
            return Response({'status':-1,'path':path,'msg':util.safe_decode(translate('should_not_change_in_path',request))})

        filename=fr.name
        #print filename 
        save_path=os.path.join(file_root,'./'+path)
        if os.path.isfile(save_path):
            msg=util.safe_decode(translate('path_is_dir',request))
            status=-1
            return Response({'file':save_path,'msg':msg,'status':status})
        elif not os.path.exists(save_path):
            os.makedirs(save_path)

        full_path=os.path.join(save_path,filename)
        #文件存在则重命名已经存在的文件
        if os.path.isfile(full_path):
            os.rename(full_path,full_path+'_'+str(time.time())) 
        
        with open(full_path,'wb') as f:
            #防止上传文件太大 分块读写到磁盘
            for chunk in fr.chunks():
               f.write(chunk) 

            status=1
            msg=util.safe_decode(translate('upload_success',request))

        return Response({'status':status,'file':full_path,'msg':msg})


    def get(self, request, args = None):
        
        for path in [request.GET.get('file',''),request.GET.get('path','')]:
            if re.match('.*\.\..*',path):
                return Response({'status':-1,'path':path,'msg':util.safe_decode(translate('should_not_change_in_path',request))})
        
        if args == 'content':
            filename = request.GET['file']

            filename = os.path.join(playbook_root,filename)
            
            content=''
            try:
                with open(filename) as f:
                    content=f.read()

                return Response({'status':1,'file':filename,'content':util.safe_decode(content)})
            except:
                return Response({'status':-1,'file':filename,'msg':util.safe_decode(translate('read_file_failed',request))})

        
        if args == 'download':
            filename = request.GET['file']

            name=os.path.basename(filename)
            filename = os.path.join(file_root,'./'+filename)

            #attachment下载文件, inline 和 attachment inline 在浏览器中显示
            showtype = ['attachment','inline', 'attachment inline'][0]

            if os.path.isfile(filename):
                file = open(filename,mode='rb')
                response=FileResponse(file)
                response['Content-Type']='application/octet-stream'
                response['Content-Disposition']='%s;filename=%s' % (showtype, name.encode('utf8'))   
                return response
            else:
                return Response({'status':-1,'file':filename,'msg':util.safe_decode(translate('path_is_not_file',request))},status=404)
       

        if args == 'list':
            root_path = request.GET['path']
            root_path = os.path.join(file_root,'./'+root_path)

            files=[]
            dirs=[]
            
            if not os.path.isfile(root_path) and os.path.exists(root_path):
                for x in os.listdir(root_path):
                    if os.path.isfile(os.path.join(root_path,x)):
                        files.append(x)
                    else:
                        dirs.append(x)
            
                files.sort()
                dirs.sort()
                return Response({'status':1,'path':root_path,'files':files,'dirs':dirs})
            else:
                return Response({'status':-1,'path':root_path,'msg':util.safe_decode(translate('path_is_not_dir',request))}) 


        if args == 'create':
            create_path = request.GET['path']

            create_path = os.path.join(file_root,'./'+create_path)
            try:
                os.makedirs(create_path)
                status=1
                msg=util.safe_decode(translate('create_success',request))
            except OSError:
                status=-1
                msg=util.safe_decode(translate('create_failed',request))

            return Response({'status':status,'path':create_path,'msg':msg})



