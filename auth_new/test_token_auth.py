# -*- coding: utf-8 -*- 
from django.test import Client, TestCase
from django.http.request import QueryDict, HttpRequest
#from django.core.handlers.wsgi import WSGIRequest
from rest_framework import exceptions

from .token_auth import request_params_check, regexp_check, choice_match_check, single_choice_rule_check_querydict, single_choice_rule_check_dict, PermanentTokenAuthentication
from .models import Account, PermanentToken, ApiInvokeRule


class TestPermanentTokenAuthentication(TestCase):

    def setUp(self):
        self.client = Client()
    
        self.account = Account.objects.create(username="super", is_superuser=True)
        self.permanent_token = PermanentToken.objects.create(
            id = 1,
            token = '675ab0baa7f747813903e8b7dbd14de3',
            username = 'super',
            
            is_validate = 1,
            validate_date = '2099-04-22 20:00:00',
            create_date = '2023-04-12 20:00:00',
            max_invoke = 9999,
            
            invoke_count = 169,
            invoke_success_count = 85,
            lastest_date =  '2023-04-20 09:33:30.825233',
            lastest_success_date = '2023-04-20 09:33:30.828086',
            
            invoke_rule_ids = '1,3'
            
        )
        ApiInvokeRule.objects.create(
            id      = 1,
            path    = '["/api/v1/home/info"]',
            source  = '["127.0.0.1"]', 
            method  = '["GET","POST"]', 
            params  = '[{"a": "aaaa", "v": "vvv"}]', 
            body    = '[{"a": "aaaa", "v": "vvv"}]'
        )
        
        ApiInvokeRule.objects.create(
            id      = 2,
            path    = '["/api/v1/home/info"]',
            source  = '["127.0.0.1"]', 
            method  = '["GET","POST"]', 
            params  = '[{"a": "xxxx", "v": "vvv"}]', 
            body    = '[{"a": "xxxx", "v": "vvv"}]'
        )
        
        ApiInvokeRule.objects.create(
            id      = 3,
            path    = '["/api/v1/home/stats"]',
            source  = '["127.0.0.1"]',
            method  = '["GET","POST"]',
            params  = '',
            body    = ''
        )
        
        ApiInvokeRule.objects.create(
            id      = 4,
            path    = '["/api/v1/target/add"]',
            source  = '["127.0.0.1"]',
            method  = '["GET","POST"]',
            params  = '',
            body    = '[{"name": "server_.*", "v": "vvv"}]'
        )
        
        self.pta = PermanentTokenAuthentication()
        self.request = HttpRequest()
        self.request.META = {'HTTP_AUTHORIZATION':'permanent_token 675ab0baa7f747813903e8b7dbd14de3'}
        
    
    def tearDown(self):
        # 自动删除册数库，不需要手动清理
        #Account.objects.all().delete()
        pass
    
    
    def test_regexp_check(self):
        self.assertTrue(regexp_check('/api/v1/home/info',  ['/api/v1/home/info','/api/v2/.*']))
        self.assertFalse(regexp_check('/api/v1/home/info', ['/x/api/v1/home/info','/api/v2/.*']))
        self.assertFalse(regexp_check('/api/v1/home/info', ['/x/api/v1/home/info/y','/api/v2/.*']))
        self.assertFalse(regexp_check('/api/v1/home/info', ['/v1/home/info','/api/v2/.*']))
        self.assertFalse(regexp_check('/api/v1/home/infox',['/api/v1/home/info','/api/v2/.*']))
        
    
    def test_single_choice_rule_check_querydict(self):
        self.assertTrue( single_choice_rule_check_querydict(QueryDict('a=aaaa&c=cccc'),{'a':'aaaa','b':'bbbb'})    )
        self.assertTrue( single_choice_rule_check_querydict(QueryDict('a=aaaa&c=cccc'),{'ab':'aaaa','b':'bbbb'})  )
        self.assertTrue( single_choice_rule_check_querydict(QueryDict('a=aaaa&a=aaaabb&c=cccc'),{'a':'aaaa.*','b':'bbbb'}) )
        self.assertFalse(single_choice_rule_check_querydict(QueryDict('a=aaaa&a=xxx&c=cccc'),{'a':'aaaa','b':'bbbb'})  )
        self.assertFalse(single_choice_rule_check_querydict(QueryDict('a=aaaa&c=cccc'),{'a':'aaaaa','b':'bbbb'})   )
        self.assertFalse(single_choice_rule_check_querydict(QueryDict('a=aaaa&b=cccc'),{'a':'aaaa','b':'bbbb'})    )
    
    
    def test_single_choice_rule_check_dict(self):
        self.assertTrue( single_choice_rule_check_dict({'a':'aaaa','c':'cccc'},{'a':'aaaa','b':'bbbb'})     )
        self.assertTrue( single_choice_rule_check_dict({'a':'aaaa','c':'cccc'},{'ab':'aaaa','b':'bbbb'})    )
        self.assertTrue( single_choice_rule_check_dict({'a':'aaaabb','c':'cccc'},{'a':'aaaa.*','b':'bbbb'}) )
        self.assertFalse(single_choice_rule_check_dict({'a':'aaaa','c':'cccc'},{'a':'aaaaa','b':'bbbb'})   )
        self.assertFalse(single_choice_rule_check_dict({'a':'aaaa','b':'cccc'},{'a':'aaaa','b':'bbbb'})    )

    
    def test_choice_match_check(self):
        self.assertTrue( choice_match_check((  QueryDict('a=aaaa&b=bbb'),  [] )) )
        self.assertTrue( choice_match_check((  QueryDict('a=aaaa&b=bbb'),  [{'a': 'aaaa', 'v': 'vvv'}] )) )
        self.assertTrue( choice_match_check((  QueryDict('a=aaaa&b=bbb'),  [{'a': 'aaaa', 'v': 'vvv'},{'a': 'abbb', 'v': 'vvv'}] )) )
        self.assertFalse( choice_match_check(( QueryDict('a=aaaa&b=bbb'),  [{'a': 'aaaa1', 'v': 'vvv'},{'a': 'abbb', 'b': 'vvv'}] )) )
        self.assertTrue( choice_match_check((  {'a':'aaaa','b':'bbbb'},    [] )) )
        self.assertTrue( choice_match_check((  {'a':'aaaa','b':'bbbb'},    [{'a': 'aaaa', 'v': 'vvv'}] )) )
        self.assertTrue( choice_match_check((  {'a':'aaaa','b':'bbbb'},    [{'a': 'aaaa', 'v': 'vvv'},{'a': 'abbb', 'v': 'vvv'}] )) )
        self.assertFalse( choice_match_check(( {'a':'aaaa','b':'bbbb'},    [{'a': 'aaaa1', 'v': 'vvv'},{'a': 'abbb', 'b': 'vvv'}] )) )
    
    
    def test_get_token_value(self):
        self.assertNotEqual(self.pta.get_token_value(self.request), None)
        self.request.META =  {}
        self.assertEqual(self.pta.get_token_value(self.request), None)
        self.request.GET = QueryDict('permanent_token=675ab0baa7f747813903e8b7dbd14de3')
        self.assertNotEqual(self.pta.get_token_value(self.request), None)
        self.request.META['HTTP_AUTHORIZATION'] = 'permanent_token'
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.pta.get_token_value(self.request)
        self.request.META['HTTP_AUTHORIZATION'] = 'permanent_token 675ab0baa7f7 47813903e8b7dbd14de3'
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.pta.get_token_value(self.request)
        
    
    def test_request_params_check(self):
        self.request.META['REMOTE_ADDR'] = '127.0.0.1'
        self.request.path = '/api/v1/home/info'
        self.request.method = 'POST'
        self.request.GET = QueryDict('a=aaaa&c=cccc')
        self.request.data = {'a':'aaaa','c':'cccc'}
        
        request_params_check([1,2], self.request)
        with self.assertRaises(exceptions.AuthenticationFailed):
            request_params_check([2,3], self.request)

    
    def test_authenticate(self):
        self.request.META['REMOTE_ADDR'] = '127.0.0.1'
        self.request.path = '/api/v1/home/info'
        self.request.method = 'POST'
        self.request.GET = QueryDict('a=aaaa&c=cccc')
        self.request.data = {'a':'aaaa','c':'cccc'}
        
        self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        PermanentToken.objects.filter(id=1).update(invoke_rule_ids='3,4')
        
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.pta.authenticate(self.request)
        
        self.request.path = '/api/v1/target/add'
        self.request.GET = QueryDict()
        self.request.data = {'name':'server_xxxxx','c':'cccc'}
        self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.data = {'name':'server_xxxxx','v':'vvv'}
        self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.data = {'name':'server_xxxxx','v':'vvvc'}
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.data = {'name':'serverx_xxxxx','c':'cccc'}
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        PermanentToken.objects.filter(id=1).update(invoke_rule_ids='2')
        self.request.path = '/api/v1/home/info'
        self.request.GET = QueryDict('a=xxxx&v=vvv')
        self.request.data = {'a':'xxxx','v':'vvv'}
        self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.GET = QueryDict('a=xxxx&v=vvv1')
        self.request.data = {'a':'xxxx','v':'vvv'}
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.GET = QueryDict('a=xxxx&v=vvv')
        self.request.data = {'a':'xxxx','v':'vvv1'}
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.assertNotEqual(self.pta.authenticate(self.request), None)
        
        self.request.META['HTTP_AUTHORIZATION'] = 'permanent_token xxxxxxxxxxxxx'
        self.assertEqual(self.pta.authenticate(self.request), None)
        
        self.request.META['HTTP_AUTHORIZATION'] = 'permanent_token 675ab0baa7f747813903e8b7dbd14de3'
        PermanentToken.objects.filter(id=1).update(username='super123')
        with self.assertRaises(exceptions.AuthenticationFailed):
            self.pta.authenticate(self.request)
            