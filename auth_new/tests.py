# -*- coding: utf-8 -*- 
import re
import json
import uuid
import requests

from django.test import Client, TestCase
from django.urls import reverse

from .models import Account


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
class TestAuth(TestCase):
    '''
    测试普通账号登陆
    '''

    @classmethod
    def setUpClass(self):
        self.login_client, self.login_info=get_login_client()


    @classmethod
    def tearDownClass(self):
        print('----------------%s done--------------------------' % self.__name__)


    def setUp(self):
        #print('begin test') 
        pass


    def tearDown(self):
       print(self.current_url, self.method, 'done') 


    def test_login(self):  
        #print(self.login_info)
        self.method='post'
        self.current_url=str(reverse('auth:login'))
        self.assertEqual(self.login_info['status'], 1)


    def test_userinfo(self):
        self.method='get'
        self.current_url=str(reverse('auth:userinfo',args=('',)))
        response = self.login_client.get(self.current_url)
        r=response.content.decode('utf8')
        r=json.loads(r)
        self.assertEqual( r['status'], 1 )


class TestAuthCas(TestCase):
    '''
    测试CAS登陆
    '''

    @classmethod
    def setUpClass(self):
        self.user="admin"                              #cas的账号
        self.password="weideguo"                       #cas的密码
        self.service='http://192.168.253.128:8080/'    #前端的回调地址，且必须与cas的回调设置一直

        self.client = Client()
        response=self.client.get(str(reverse('auth:cas',args=('login',)))+'?service='+self.service)

        try:
            r=response.content.decode('utf8')
            r=json.loads(r)
        except:
            print(r)

        self.cas_login_url=r.get('cas_login_url')
        if not self.cas_login_url:
            print(response.content.decode('utf8'))


    @classmethod
    def tearDownClass(self):
        print('----------------%s done--------------------------' % self.__name__)


    def tearDown(self):
       print(self.current_url, self.method, 'done') 



    def test_get_cas(self):
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('login',)))
        

    def test_cas_login(self):
        self.method='get'
        self.current_url=str(reverse('auth:cas',args=('serviceValidate',)))
        if self.cas_login_url:

            #print(self.cas_login_url)
            #模拟前端访问
            response=requests.get(self.cas_login_url)
            
            y=response.headers['set-cookie']
            csrftoken=re.search('(?<=csrftoken=).+?(?=;)',y).group()
            
            r=response.content.decode('utf8')
            h_c_html=re.search('<input type="hidden" name="csrfmiddlewaretoken".*',r).group() 
            csrfmiddlewaretoken=re.search('(?<=value=").+?(?=")',h_c_html).group()
            csrfmiddlewaretoken=str(csrfmiddlewaretoken)

            data={'csrfmiddlewaretoken':csrfmiddlewaretoken,'username':self.user, 'password':self.password}
            cookies={'csrftoken':csrftoken}
            
            #登陆cas，获取重定向信息
            r=requests.post(self.cas_login_url,data=data,cookies=cookies,allow_redirects=False)
            try:
                redirect_url=r.headers['location']
            except:
                #没有重定向信息 则可能是设置的 user password service 错误
                raise Exception('cas login failed, check setting of [ user password service ] ')

            ticket=''
            for raw_param in redirect_url.split('?')[-1].split('&'):
                if re.search('(?<=ticket=).*',raw_param):
                    ticket=re.search('(?<=ticket=).*',raw_param).group()

            self.assertTrue(ticket)
            #print(ticket)

            #将获取的ticket让后端验证是否登陆成功
            url=self.current_url+'?ticket=%s&service=%s' % (ticket,self.service)
            response=self.client.get(url)
            r=response.content.decode('utf8')
            r=json.loads(r)
            if r['status'] != 1:
                print(r)

            self.assertEqual( r['status'], 1 )
