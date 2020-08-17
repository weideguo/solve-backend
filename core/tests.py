# -*- coding: utf-8 -*- 
import json
from django.test import Client, TestCase
from django.urls import reverse

#from auth_new.tests import get_login_client
from auth_new.tests import LoginTestCase


#测试用例
class TestHome(LoginTestCase):
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



class TestOrder(LoginTestCase):
    def test_get_order(self):
        self.method='get'
        self.current_url=str(reverse('order',args=('',)))
        r=self.login_client.get(self.current_url)
        self.assertTrue(r.status_code,200)


class TestTarget(LoginTestCase):
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


