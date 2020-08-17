# -*- coding: utf-8 -*- 
import re
import json
import uuid
import requests

from django.test import Client, TestCase
from django.urls import reverse

from .models import Account


class BaseTestCase(TestCase):
    @classmethod
    def tearDownClass(self):
        print('----------------%s done--------------------------' % self.__name__)


    def setUp(self):
        #print('begin test') 
        pass

    def tearDown(self):
       print(self.current_url, self.method, 'done') 


class LoginTestCase(BaseTestCase):

    @classmethod
    def setUpClass(self):
        self.login_client, self.login_info=get_login_client()


def get_login_client():
    '''
    获取登录client
    '''
    client = Client()
    #创建随机的测试账号
    user=uuid.uuid1().hex
    password=uuid.uuid1().hex
    Account.objects.create_user(
        username=user,
        password=password)
    
    data={'username':user,'password':password}
    response = client.post(str(reverse('auth:login')),data=data)
    login_info={}
    try:
        r=response.content.decode('utf8')
        r=json.loads(r)
    except:
        print(r)

    login_info=r
    token=login_info['token']

    return Client(HTTP_AUTHORIZATION='JWT '+token), login_info


#测试用例
class TestAuth(BaseTestCase):
    '''
    测试普通账号登陆
    '''

    @classmethod
    def setUpClass(self):
        self.login_client, self.login_info=get_login_client()

    
    def test_login(self):  
        #print(self.login_info)
        self.method='post'
        self.current_url=str(reverse('auth:login'))
        self.assertEqual(self.login_info['status'], 1)


    def test_userinfo_get(self):
        self.method='get'
        self.current_url=str(reverse('auth:userinfo',args=('',)))
        response = self.login_client.get(self.current_url)
        r=response.content.decode('utf8')
        r=json.loads(r)
        #print(r)
        self.assertEqual( r['status'], 1 )
    
    def test_userinfo_put(self):
        self.method='put'
        self.current_url=str(reverse('auth:userinfo',args=('',)))
        #data={'username':'testuser','new':'my_new_password'}
        data={'username':'testuser','new':'xxxxx'}
        response = self.login_client.put(self.current_url,json.dumps(data),content_type='application/json')
        r=response.content.decode('utf8')
        #print(r)
        r=json.loads(r)
        self.assertTrue( r['status'])
    
    def test_userinfo_post(self):
        self.method='post'
        self.current_url=str(reverse('auth:userinfo',args=('',)))
        data={'username':'testuser','password':'my_password'}
        response = self.login_client.post(self.current_url,data=data)
        r=response.content.decode('utf8')
        #print(r)
        r=json.loads(r)
        self.assertEqual( r['status'], 1 )
    

    def test_userinfo_delete(self):
        self.method='delete'
        self.current_url=str(reverse('auth:userinfo',args=('testuser',)))
        #print(self.current_url)
        response = self.login_client.delete(self.current_url)
        r=response.content.decode('utf8')
        #print(r)
        r=json.loads(r)
        self.assertEqual( r['status'], 1 )

#################################################################################################

def get_cas_login_url(cls):
    cls.client = Client()
    response=cls.client.get(str(reverse('auth:cas',args=('login',)))+'?service='+cls.service)
    try:
        r_raw=response.content.decode('utf8')
        r=json.loads(r_raw)
    except:
        print(r)
    cas_login_url= r.get('cas_login_url')
    if not cas_login_url:
        print(r_raw)

    return cas_login_url


def get_cas_ticket(cls):
    '''
    模拟前端页面登陆获取cas的ticket
    '''
    response=requests.get(cls.cas_login_url)
    
    y=response.headers['set-cookie']
    csrftoken=re.search('(?<=csrftoken=).+?(?=;)',y).group()
    
    r=response.content.decode('utf8')
    h_c_html=re.search('<input type="hidden" name="csrfmiddlewaretoken".*',r).group() 
    csrfmiddlewaretoken=re.search('(?<=value=").+?(?=")',h_c_html).group()
    csrfmiddlewaretoken=str(csrfmiddlewaretoken)
    
    data={'csrfmiddlewaretoken':csrfmiddlewaretoken,'username':cls.user, 'password':cls.password}
    cookies={'csrftoken':csrftoken}
    
    #登陆cas，获取重定向信息
    r=requests.post(cls.cas_login_url,data=data,cookies=cookies,allow_redirects=False)
    try:
        redirect_url=r.headers['location']
    except:
        #没有重定向信息 则可能是设置的 user password service 错误
        raise Exception('cas login failed, check setting of [ user password service ] ')
    
    ticket=''
    for raw_param in redirect_url.split('?')[-1].split('&'):
        if re.search('(?<=ticket=).*',raw_param):
            ticket=re.search('(?<=ticket=).*',raw_param).group()

    return ticket


def cas_auth(cls,pgtUrl=''):
    '''将获取的ticket让后端验证是否登陆成功'''
    if not cls.cas_login_url:
        return None
    
    ticket=get_cas_ticket(cls)
    #cls.assertTrue(ticket)
    #print(ticket)
    cas_valid_url=str(reverse('auth:cas',args=('serviceValidate',)))
    if pgtUrl:
        url=cas_valid_url+'?ticket=%s&service=%s&pgtUrl=%s' % (ticket,cls.service,pgtUrl)
    else:
        url=cas_valid_url+'?ticket=%s&service=%s' % (ticket,cls.service)
    #print(url)
    response=cls.client.get(url)
    r=response.content.decode('utf8')
    r=json.loads(r)
    if r['status'] != 1:
        print(r)

    #print(r)
    #cls.assertEqual( r['status'], 1 )
    token=r['token']
    return Client(HTTP_AUTHORIZATION='JWT '+token)



user="admin"                              #cas的账号
password="weideguo"                       #cas的密码
service='http://192.168.253.128:8080/'    #前端的回调地址，且必须与cas的回调设置一致
proxy_callback='https://127.0.0.1:9000/api/v1/cas/callback'                #自己的cas回调地址，用于当前服务连接其他服务（需要为https）
another_service ='https://192.168.253.128:9000/api/v1/cas/proxyValidate'   #要连接的其他服务的验证地址，用于当前服务连接其他服务（需要为https，且cas中设置好允许的地址）

class TestAuthCas(BaseTestCase):
    '''
    测试CAS登陆
    '''

    @classmethod
    def setUpClass(self):
        self.user=user          
        self.password=password  
        self.service=service    

        self.cas_login_url=get_cas_login_url(self)

        self.cas_login_client=cas_auth(self)


    def test_get_cas(self):
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('login',)))
        

    def test_cas_login(self):
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('serviceValidate',)))
            

    def test_cas_logout(self):
        '''
        退出cas
        '''
        self.method='get'
        self.current_url=str(reverse('auth:logout'))
        if self.cas_login_url and self.cas_login_client:

            
            r=self.cas_login_client.get(self.current_url+'?service='+self.service)
            r=json.loads(r.content.decode('utf8'))
            self.assertEqual( r['status'], 1 )


class TestAuthCasProxy(BaseTestCase):
    '''测试这个必须先启动服务以提供回调地址'''
    @classmethod
    def setUpClass(self):
        self.user=user          
        self.password=password  
        self.service=service    
        self.proxy_callback=proxy_callback

        self.cas_login_url=get_cas_login_url(self)
        self.cas_login_client=cas_auth(self, self.proxy_callback)

    def test_proxy_callback(self):
        '''
        本地用于接收cas发来proxy pgtId/pgtIou的回调地址
        pgtId/pgtIou用于获取proxy的ticket
        proxy的ticket可用于向其他服务发出登陆请求（其他服务需要共同连接统一cas，且实现验证ticket的接口）
        '''
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('callback',)))
        client = Client()
        r=client.get(self.current_url+'?pgtId='+uuid.uuid1().hex+'&pgtIou=you_should_delete_this')
        self.assertTrue(r.status_code,200)

    def test_cas_login_with_proxy(self):
        '''使用cas登陆并带上对其他代理访问的地址'''
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('serviceValidate',)))

    def test_auth_other(self):
        '''当前服务cas登陆后获取其他服务的token'''
        self.method='get'
        self.current_url='call_other_service_url_demo'
        from auth_new.wrapper import get_service_token
        get_service_token(another_service,verify=False) 
        #由于使用测试数据库查询不出结果，以下测试需要进入的django shell手动运行
        print('run this command in django shell:')
        print('from auth_new.wrapper import get_service_token;get_service_token("%s",verify=False)' % another_service)
        

