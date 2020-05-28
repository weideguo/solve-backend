#coding:utf8
import json
from django.test import Client, TestCase

from .models import Account

base_url='/api/v1/'

#测试用例
class TestAuth(TestCase):
    '''
    测试普通账号登陆
    '''

    @classmethod
    def setUpClass(self):
        self.client = Client()
        self.user='testuser'
        self.password='testpassword'
        Account.objects.create_user(
            username=self.user,
            password=self.password)
        
        data={'username':self.user,'password':self.password}
        response = self.client.post(base_url+'login/',data=data)
        self.login_info={}
        try:
            r=response.content.decode('utf8')
            r=json.loads(r)
        except:
            print(r)

        self.login_info=r
        self.token=self.login_info['token']

        self.login_client=Client(HTTP_AUTHORIZATION='JWT '+self.token)


    @classmethod
    def tearDownClass(self):
        print('----------------%s done--------------------------' % 'TestAuth')


    def setUp(self):
        print('begin test')        


    def tearDown(self):
        print('test done')


    def test_login(self):  
        #print(self.login_info)
        self.assertEqual(self.login_info['status'], 1)


    def test_userinfo(self):
        '''
        #只能对使用django的登陆机制才能用？
        self.superuser = Account.objects.create(username='super', is_superuser=True)
        self.client.force_login(self.superuser1)
        '''
        #response = self.client.get(base_url+'userinfo/',HTTP_AUTHORIZATION='JWT '+self.token)
        response = self.login_client.get(base_url+'userinfo/')
        r=response.content.decode('utf8')
        r=json.loads(r)
        self.assertEqual( r['status'], 1 )


class TestAuthCas(TestCase):
    '''
    测试CAS登陆
    '''

    @classmethod
    def setUpClass(self):
        self.client = Client()

    @classmethod
    def tearDownClass(self):
        print('----------------%s done--------------------------' % 'TestAuthCas')


    def test_get_cas(self):
        service='127.0.0.1:9000'
        #print(base_url+'cas/login?service='+service)
        response=self.client.get(base_url+'cas/login?service='+service)
        r=response.content.decode('utf8')
        r=json.loads(r)
        #print(r)
        self.assertEqual( r['status'], 1 )
        

    def test_cas_login(self):
        ticket='ST-1590631030-1BVq1UYuNNuEYoUZseJkqejAYlZHX8hi' #前端访问CAS后获取到的ticket
        service='http://192.168.253.128:8080/%23/login'         #前端访问CAS后的回调地址
        url=base_url+'cas/serviceValidate?ticket=%s&service=%s' % (ticket,service)
        response=self.client.get(url)
        r=response.content.decode('utf8')
        #print(url)
        print(r)
        r=json.loads(r)
       
        #self.assertEqual( r['status'], 1 )