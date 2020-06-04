# solve-backend #


使用solve的web后端。通过jwt记录账号登陆状态。


running
--------------
### dependency servers ###
* redis (>= 2.0.0)
* solve

### version support ###
* python 2.7
* python 3.5

### prerun ###
```shell
#sh set_secret_key.sh               #重新生成SECRET_KEY于django的配置文件
python manage.py resetsecretkey     #重新生成SECRET_KEY于django的配置文件
vim deploy.conf                     #设置redis、mongodb、cas 以及其他相关参数
#首次运行初始化
python manage.py makemigrations     #创建数据库迁移文件
python manage.py migrate            #使用迁移文件初始化数据库
python manage.py createsuperuser    #创建账号
export LC_ALL=en_US.UTF-8           #中文支持
```

### start ###
```shell
nohup python manage.py runserver 127.0.0.1:8000 &

#正式环境使用gunicorn 提供更好性能
gunicorn setting.wsgi:application -b 0.0.0.0:8000 
gunicorn setting.wsgi:application -c gunicorn.conf -p solve_backend.pid -n solve_backend
```

### test ###
```shell
#使用test目录下的测试样例
cd test             
curl http://...
#使用测试框架
python manage.py test auth_new
python manage.py test core
python manage.py test
```