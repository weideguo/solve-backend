#coding:utf8
import os
import sys
import time
from rest_framework.response import Response
from django.http import FileResponse

from auth_new import baseview
from libs import util, redis_pool
from libs.wrapper import error_capture
from conf import config

#file_root=config.file_root
cp=util.getcp()
file_root=cp.get('common','file_root')

class File(baseview.BaseView):
    '''
    关于文件的操作
    中文路径 文件名支持 export LC_ALL=en_US.UTF-8
    '''
    @error_capture
    def post(self, request, args = None):
        fr=request.FILES.get('file',None)      #curl "$url" -F "file=@/root/x.txt"  
        path=request.GET['path']    
        filename=fr.name
        #print filename 
        save_path=os.path.join(file_root,'./'+path)
        if os.path.isfile(save_path):
            msg=util.safe_decode('路径为文件')
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
            msg=util.safe_decode('上传成功')

        return Response({'status':status,'file':full_path,'msg':msg})


    @error_capture
    def get(self, request, args = None):
        if args == 'download':
            filename = request.GET.get('file')
            name=os.path.basename(filename)
            filename = os.path.join(file_root,'./'+filename)
            
            if os.path.isfile(filename):
                file = open(filename,mode='rb')
                response=FileResponse(file)
                response['Content-Type']='application/octet-stream'
                response['Content-Disposition']='attachment;filename="%s' % name.encode('utf8')   #inline 和 attachment inline 在浏览器中显示
                return response
            else:
                return Response({'status':-1,'file':filename,'msg':util.safe_decode('路径不为文件')})
       

        if args == 'list':
            root_path = request.GET.get('path')
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
                return Response({'status':-1,'path':root_path,'msg':util.safe_decode('路径不为目录')}) 


        if args == 'create':
            create_path = request.GET.get('path')
            create_path = os.path.join(file_root,'./'+create_path)
            try:
                os.makedirs(create_path)
                status=1
                msg=util.safe_decode('创建成功')
            except OSError:
                status=-1
                msg=util.safe_decode('创建失败')

            return Response({'status':status,'path':create_path,'msg':msg})



