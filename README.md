# solve-backend #

[![Python 3.7|3.9](https://img.shields.io/badge/python-3.7%7C3.9-blue.svg)](https://github.com/weideguo/solve-backend) 
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/weideguo/solve-backend/blob/master/LICENSE) 


使用solve的web后端。通过jwt记录账号登陆状态。


running
--------------
### dependency servers ###
* redis (>= 2.0.0)
* solve

### prerun ###
```shell
#首次运行初始化
vim deploy.conf                     #设置redis、mongodb、cas 以及其他相关参数
#sh set_secret_key.sh               #重新生成SECRET_KEY于django的配置文件
python manage.py resetsecretkey     #重新生成SECRET_KEY于django的配置文件 使用该命令需要先设置redis
python manage.py makemigrations     #创建数据库迁移文件
python manage.py migrate            #使用迁移文件初始化数据库
python manage.py createsuperuser    #创建账号
python set_config.py                #初始化执行对象、执行模板等的一些默认配置，这些配置也可以在web界面重新修改
```

### start ###
```shell
export LC_ALL=en_US.UTF-8           #中文支持
# 持久化进程
nohup python durable_server.py &
# web进程
nohup python manage.py runserver 127.0.0.1:8000 &

#正式环境使用gunicorn 提供更好性能
gunicorn setting.wsgi:application -b 0.0.0.0:8000 
gunicorn setting.wsgi:application -c gunicorn.conf -p solve_backend.pid -n solve_backend
```

### multi language ###
语言选择由前端请求的http头 Accept-Languague （django request.META['HTTP_ACCEPT_LANGUAGUE'）控制  
默认使用中文 zh_cn/zh-CN  即对应 zh_Hans，前端的http头不区分大小写以及下划线，以及可以只匹配前部
```shell
# 后端设置
# python manage.py makemessages -l en
python manage.py makemessages -l zh_Hans    #设置语言包，每次修改要翻译的字符串时需要运行
python manage.py compilemessages            #修改.po文件后需要运行
```

### test ###
```shell
#使用test目录下的测试样例
cd test             
curl http://...
#使用测试框架 执行前请先配置好文件deploy.conf
python manage.py test auth_new.test_token_auth
python manage.py test auth_new
python manage.py test core
python manage.py test

#统计测试覆盖率
#pip install coverage    #安装coverage
#清除之前的统计信息
coverage erase
#使用django test模块运行
coverage run manage.py test
#生成报告
coverage report
```