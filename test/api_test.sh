###############################################################################################################
#################  部分api的测试  #################

#登录 
curl "http://127.0.0.1:8000/api/v1/login/" -d "username=admin&password=weideguo"

curl -H "Content-Type:application/json" -H "Accept:application/json"  -d "{\"username\":\"admin\",\"password\":\"weideguo\"}" "http://127.0.0.1:8000/api/v1/login/"

curl -H "Content-Type:application/json" -H "Accept:application/json"  -d '{"username":"admin","password":"weideguo"}' "http://127.0.0.1:8000/api/v1/login/"

xx=`curl "http://127.0.0.1:8000/api/v1/login/" -d "username=admin&password=weideguo" | grep -oP "(?<=token\":\").*?(?=\")"`

###############################################################################################################
#首页

curl -k "https://127.0.0.1:443/api/v1/home/info" -H "Authorization:Bearer ${xx}"    #https使用 不验证证书

curl  "http://127.0.0.1:8000/api/v1/home/info" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/home/stats" -H "Authorization:Bearer ${xx}"





#用户管理
curl  "http://127.0.0.1:8000/api/v1/userinfo/?page=1&pagesize=16" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/userinfo/" -H "Authorization:Bearer ${xx}"  -X POST -d "username=weideguo111&password=weideguo"

curl  "http://127.0.0.1:8000/api/v1/userinfo/" -H "Authorization:Bearer ${xx}"  -X PUT -d "username=weideguo111&new=weideguo"

curl  "http://127.0.0.1:8000/api/v1/userinfo/${username}" -H "Authorization:Bearer ${xx}"  -X DELETE 




#工单增改查
curl "http://127.0.0.1:8000/api/v1/order/?page=1&pagesize=16" -H "Authorization:Bearer ${xx}" 


curl "http://127.0.0.1:8000/api/v1/order/detail?workid=job_0ba06dba38b311e9add3000c29e7008f" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/?workid=job_0ba06dba38b311e9add3000c29e7008f" -H "Authorization:Bearer ${xx}"  -X DELETE 

curl "http://127.0.0.1:8000/api/v1/order/abort?cluster_id=0ba06dba38b311e9add3000c29e7008f" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/exelist?id=log_cluster_904b1b827aa811e9a1c8005056b64b9c" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/exedetail?id=904b7b727aa811e980d5005056b64b9c" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/order/run_target_list?workid=job_03799d7ed68411ec81cc005056337d90&target_name=cluster1" -H "Authorization:Bearer ${xx}"







#执行对象管理
curl "http://127.0.0.1:8000/api/v1/target/get?filter=host*&page=1" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/target/del?target=t" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/target/add" -H "Authorization:Bearer ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=af"

curl "http://127.0.0.1:8000/api/v1/target/update" -H "Authorization:Bearer ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=afd"

curl "http://127.0.0.1:8000/api/v1/target/info?filter=host" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/target/tree?name=host_windows_10.10.19.13" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/executioninfo/get?filter=pre_exec:*&page=1" -H "Authorization:Bearer ${xx}"




#主机管理
curl "http://127.0.0.1:8000/api/v1/host/online" -H "Authorization:Bearer ${xx}"


#执行管理
curl "http://127.0.0.1:8000/api/v1/session/?filter=xxxx" -H "Authorization:Bearer ${xx}"
curl "http://127.0.0.1:8000/api/v1/session/extend?filter=exec:%E6%B5%8B%E8%AF%95playbook%E9%A6%96%E9%83%A8session%E8%AF%B4%E6%98%8E" -H "Authorization:Bearer ${xx}"

curl "http://127.0.0.1:8000/api/v1/execution/?filter=eweas123124" -H "Authorization:Bearer ${xx}" -X POST -d "name=server_db12334987sd&a=daf&b=af"
curl "http://127.0.0.1:8000/api/v1/execution/?filter=exec:%E8%8E%B7%E5%8F%96%E5%86%85%E7%BD%91ip&debug=1" -H "Authorization:Bearer ${xx}" -X POST -d ""


curl "http://127.0.0.1:8000/api/v1/session/?filter=exec:%E6%89%A7%E8%A1%8Cshell" -H "Authorization:Bearer ${xx}" -d "cmd=ls -altr /root"

curl "http://127.0.0.1:8000/api/v1/session/temp" -H "Authorization:Bearer ${xx}" -d "cmd=ls -altr /root"

curl "http://127.0.0.1:8000/api/v1/fast/" -H "Authorization:Bearer ${xx}" -X POST -d  "spliter=|&parallel=true&exeinfo=192.168.253.128      |  whoami    | pwd\n192.168.253.128      |  whoami    | pwd&playbook=[{{_1}}]     \necho {{_2}}  \necho {{_3}}  "

curl "http://127.0.0.1:8000/api/v1/pauseRun/?target_id=8d0e0604cfda11eaa9cc000c295dd589&type=0" -H "Authorization:Bearer ${xx}" 


curl "http://127.0.0.1:8000/api/v1/global/?target_id=6cec337832e911ec8f80005056337d90" -H "Authorization:Bearer ${xx}" -d "xx=123&&yy=abc"


#文件管理

curl  "http://127.0.0.1:8000/api/v1/file/?path=./" -F "file=@/root/xxx.sh"  -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/download?file=./新建文本文档.txt" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/list?path=/.//mysql-8.0.11-linux-glibc2.12-x86_64/share" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/create?path=aaa/bbb/ccc" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/content?file=/data/gameTools/new_update/11111/django_view" -H "Authorization:Bearer ${xx}"

curl  "http://127.0.0.1:8000/api/v1/file/content?file=./11111/django_view&relative=1" -H "Authorization:Bearer ${xx}"

#config
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_types" -H "Authorization:Bearer ${xx}"
#多语言
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_types" -H "Authorization:Bearer ${xx}" -H "Accept-Language:en-US"
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_types" -H "Authorization:Bearer ${xx}" -H "Accept-Language:zh-CN"

#直接提提交非string类型需要指明header
#如何传list？
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerqqddddyyy111&type=list" -H "Accept:application/json" -H "Authorization:Bearer ${xx}" -X POST -d "[\"a在\",\"b\",\"c\"]"
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerqqqq&type=string" -H "Authorization:Bearer ${xx}" -X POST -d "中文也可以"
curl  "http://127.0.0.1:8000/api/v1/config/?key=job_werwerq" -H "Authorization:Bearer ${xx}" -X POST -d "id=1111&opid=123"



#dura
curl  "http://127.0.0.1:8000/api/v1/dura/?id=job_3d10ade82b8711ea82d8000c295dd589" -H "Authorization:Bearer ${xx}"




#test
curl  "http://127.0.0.1:8000/api/v1/test/" -H "Authorization:Bearer ${xx}"


# permanent_token
permanent_token="675ab0baa7f747813903e8b7dbd14de3"
curl  "http://127.0.0.1:8000/api/v1/home/info" -H "Authorization:permanent_token ${permanent_token}"

curl  "http://127.0.0.1:8000/api/v1/home/info?permanent_token=${permanent_token}"


curl "http://127.0.0.1:8000/api/v1/target/add?a=aaa&b=bbb" -H "Authorization:permanent_token ${permanent_token}" -H "Content-Type:application/json" -d "{\"name\":\"server_db12334987\",\"sda\":\"daf\",\"b\":\"af\"}"

curl "http://127.0.0.1:8000/api/v1/target/update" -H "Authorization:permanent_token ${permanent_token}" -X POST -d "name=server_db12334987sd&a=daf&b=afd"


