# 登录认证模块 #

> 前后端分离的登陆认证模块，基于jwt维持前后端的登陆状态
> 可选择使用CAS做集中账号管理


## 设置 ##
```python
#setting.py

#使用的认证表对应的models
AUTH_USER_MODEL = 'auth_new.Account'

INSTALLED_APPS += ['rest_framework','auth_new']

# 用于auth_new模块
"""
CAS协议提供的接口：
login                #登陆(前端使用)
logout               #登出(前端使用)
validate             #验证ticket 返回text格式 (后端使用)
serviceValidate      #验证ticket 返回xml格式  (后端使用)
"""
#cas地址的string对象
CAS_URL='libs.wrapper.cas_url'
#用于翻译的函数
TRANSLATE='libs.util.translate'
```
```python
#urls.py
urlpatterns += [url(r'^api/v1/', include('auth_new.urls'))]
```

## 测试 ##
```python
#获取pgtId，pgtId可以反复使用，在过期后再获取新的
my_frontend='http://192.168.59.132:8080/'                            #前端获取ticket时的设置的回调地址
my_backend ='https://192.168.59.132:9000/api/v1/cas/serviceValidate' #后端处理serviceValidate的接口
my_callback='https://192.168.59.132:9000/api/v1/cas/callback'        #接收cas回调的后端接口，由此会获取新的pgtId，需要为https

#由前端获取ticket，如直接在浏览器中访问
#http://192.168.59.132:9095为cas的根路径
#http://192.168.59.132:9095/cas/login?service=http://192.168.59.132:8080/#/login
ticket='ST-1575617640-ByqBYrzELgcnA256x8ERt9MURmSEhNjE'    

#如果没有pgtUrl参数，则当作普通的cas登陆，登陆信息不能用于连接其他的app
#带pgtUrl参数，即登陆该app之后，要访问其他app的接口，双方使用同一个cas且设置代理，则可以使用当前登陆的账号信息（不是通过保存账号密码）直接连接其他app，而不需要再次登陆
#后端调用cas，验证ticket，获取pgtId
requests.get('%s?ticket=%s&service=%s&pgtUrl=%s' % (my_backend,ticket,my_frontend,my_callback), verify=0).text

####################################################
#获取其他app的token
from auth_new.wrapper import get_service_token
service_proxyValidate='http://192.168.59.132:7000/api/v1/cas/proxyValidate'          #要连接的app处理proxyValidate的接口
get_service_token(service_proxyValidate,verify=0)

targetService='http://192.168.59.132:7000'                 
#不指定targetService时，默认为service_proxyValidate的根路径
get_service_token(service_proxyValidate,targetService=targetService,verify=0)
```

