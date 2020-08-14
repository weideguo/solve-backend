# -*- coding: utf-8 -*- 
import json
from django.test import Client, TestCase
from django.urls import reverse

from auth_new.tests import get_login_client


class BaseTestCase(TestCase):

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
       print(self.current_url, self.method,  'done') 



#测试用例
class TestHome(BaseTestCase):
    def test_info(self): 
        self.method='get'
        self.current_url=str(reverse('home',args=('info',)))
        r=self.login_client.get(self.current_url)
        #r=json.loads(r.content.decode('utf8'))
        #print(r)
        #self.assertTrue(r['status'] > 0)
        #print(r.status_code)
        self.assertTrue(r.status_code,200)


    def test_stats(self): 
        self.method='get'
        self.current_url=str(reverse('home',args=('stats',)))
        r=self.login_client.get(self.current_url)
        self.assertTrue(r.status_code,200)



class TestOrder(BaseTestCase):
    def test_get_order(self):
        self.method='get'
        self.current_url=str(reverse('order',args=('',)))
        r=self.login_client.get(self.current_url)
        self.assertTrue(r.status_code,200)


class TestTarget(BaseTestCase):
    def test_get_target(self):
        self.method='get'
        self.current_url=str(reverse('target',args=('get',)))
        r=self.login_client.get(self.current_url+'?filter=host*')
        #print(r.content)
        self.assertTrue(r.status_code,200)

    def test_get_target_info(self):
        self.method='get'
        self.current_url=str(reverse('target',args=('info',)))
        r=self.login_client.get(self.current_url+'?filter=const*')
        #print(r.content)
        self.assertTrue(r.status_code,200)


