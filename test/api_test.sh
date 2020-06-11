###############################################################################################################
#################  部分api的测试  #################

#登录 
curl "http://127.0.0.1:8000/api/v1/login/" -d "username=admin&password=weideguo"

curl -H "Content-Type:application/json" -H "Accept:application/json"  -d "{\"username\":\"admin\",\"password\":\"weideguo\"}" "http://127.0.0.1:8000/login/"

xx=`curl "http://127.0.0.1:8000/api/v1/login/" -d "username=admin&password=weideguo" | grep -oP "(?<=token\":\").*?(?=\")"`

###############################################################################################################
#首页

curl -k "https://127.0.0.1:443/api/v1/home/info" -H "Authorization:JWT ${xx}"    #https使用 不验证证书

curl  "http://127.0.0.1:8000/api/v1/home/info" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/home/stats" -H "Authorization:JWT ${xx}"





#用户管理
curl  "http://127.0.0.1:8000/api/v1/userinfo/?page=1&pagesize=16" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/userinfo/" -H "Authorization:JWT ${xx}"  -X POST -d "username=weideguo111&password=weideguo"

curl  "http://127.0.0.1:8000/api/v1/userinfo/" -H "Authorization:JWT ${xx}"  -X PUT -d "username=weideguo111&new=weideguo"

curl  "http://127.0.0.1:8000/api/v1/userinfo/${username}" -H "Authorization:JWT ${xx}"  -X DELETE 




#工单增改查
curl "http://127.0.0.1:8000/api/v1/order/?page=1&pagesize=16" -H "Authorization:JWT ${xx}" 


curl "http://127.0.0.1:8000/api/v1/order/detail?workid=job_0ba06dba38b311e9add3000c29e7008f" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/del?workid=job_0ba06dba38b311e9add3000c29e7008f" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/abort?cluster_id=0ba06dba38b311e9add3000c29e7008f" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/exelist?id=log_cluster_904b1b827aa811e9a1c8005056b64b9c" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/exedetail?id=904b7b727aa811e980d5005056b64b9c" -H "Authorization:JWT ${xx}"









#执行对象管理
curl "http://127.0.0.1:8000/api/v1/target/get?filter=host*&page=1" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/target/del?target=t" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/target/add" -H "Authorization:JWT ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=af"

curl "http://127.0.0.1:8000/api/v1/target/update" -H "Authorization:JWT ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=afd"

curl "http://127.0.0.1:8000/api/v1/target/info?filter=host" -H "Authorization:JWT ${xx}"


curl "http://127.0.0.1:8000/api/v1/executioninfo/get?filter=pre_exec:*&page=1" -H "Authorization:JWT ${xx}"




#主机管理
curl "http://127.0.0.1:8000/api/v1/host/online" -H "Authorization:JWT ${xx}"


#执行管理
curl "http://127.0.0.1:8000/api/v1/session/?filter=xxxx" -H "Authorization:JWT ${xx}"
curl "http://127.0.0.1:8000/api/v1/session/extend?filter=exec:%E6%B5%8B%E8%AF%95playbook%E9%A6%96%E9%83%A8session%E8%AF%B4%E6%98%8E" -H "Authorization:JWT ${xx}"

curl "http://127.0.0.1:8000/api/v1/execution/?filter=eweas123124" -H "Authorization:JWT ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=af"


curl "http://127.0.0.1:8000/api/v1/session/?filter=exec:%E6%89%A7%E8%A1%8Cshell" -H "Authorization:JWT ${xx}" -d "cmd=ls -altr /root"

curl "http://127.0.0.1:8000/api/v1/session/temp" -H "Authorization:JWT ${xx}" -d "cmd=ls -altr /root"

curl "http://127.0.0.1:8000/api/v1/fast/" -H "Authorization:JWT ${xx}" -X POST -d  "spliter=|&parallel=true&exeinfo=192.168.253.128      |  whoami    | pwd\n192.168.253.128      |  whoami    | pwd&playbook=[{{_1}}]     \necho {{_2}}  \necho {{_3}}  "

#文件管理

curl  "http://127.0.0.1:8000/api/v1/file/?path=./" -F "file=@/root/xxx.sh"  -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/download?file=./新建文本文档.txt" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/list?path=/.//mysql-8.0.11-linux-glibc2.12-x86_64/share" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/create?path=aaa/bbb/ccc" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/content?file=/data/gameTools/new_update/11111/django_view" -H "Authorization:JWT ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/content?file=./11111/django_view&relative=1" -H "Authorization:JWT ${xx}"

#config
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_types" -H "Authorization:JWT ${xx}"

#直接提提交非string类型需要指明header
#如何传list？
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerqqddddyyy111&type=list" -H "Accept:application/json" -H "Authorization:JWT ${xx}" -X POST -d "[\"a在\",\"b\",\"c\"]"
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerqqqq&type=string" -H "Authorization:JWT ${xx}" -X POST -d "中文也可以"
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerq" -H "Authorization:JWT ${xx}" -X POST -d "id=1111&opid=123"



#dura
curl  "http://127.0.0.1:8000/api/v1/dura/?id=job_3d10ade82b8711ea82d8000c295dd589" -H "Authorization:JWT ${xx}"




#test
curl  "http://127.0.0.1:8000/api/v1/test/" -H "Authorization:JWT ${xx}"


