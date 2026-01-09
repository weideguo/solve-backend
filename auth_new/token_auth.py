# -*- coding: utf-8 -*- 
import re
import json
import datetime

from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.core.cache import cache
from rest_framework import exceptions,HTTP_HEADER_ENCODING
from rest_framework.authentication import (
    BaseAuthentication, get_authorization_header
)

from .models import PermanentToken,ApiInvokeRule


class PermanentTokenAuthentication(BaseAuthentication):
    """
    持久token认证
    """
    def authenticate(self, request):
        """
        自行查询数据库然后验证
        """
        token_value = get_token_value(request,auth_header_prefix='permanent_token')
        if token_value is None:
            return None

        token_value = str(token_value)
        permanent_token = PermanentToken.objects.filter(token=token_value)
        _permanent_token = permanent_token.first()
        if _permanent_token:
            permanent_token.update(lastest_date=datetime.datetime.now(), invoke_count=F('invoke_count')+1)
        else:
            return None
        
        username             = _permanent_token.username   
        
        _invoke_rule_ids     = _permanent_token.invoke_rule_ids.split(",") if _permanent_token.invoke_rule_ids       else []
        invoke_rule_ids      = [int(i) for i in _invoke_rule_ids]
        
        max_invoke           = _permanent_token.max_invoke
        invoke_success_count = _permanent_token.invoke_success_count
        
        is_validate          = _permanent_token.is_validate      
        validate_date        = _permanent_token.validate_date    
        
        if not invoke_rule_ids:
            msg = _('permanent token do not work as invoke rule is null')
            raise exceptions.AuthenticationFailed(msg)
        
        # 对请求参数进行校验
        request_params_check(invoke_rule_ids, request)
        
        if max_invoke - invoke_success_count < 1:
            msg = _('permanent token exceed invoke limit')
            raise exceptions.AuthenticationFailed(msg)
        
        if is_validate == 0:
            msg = _('permanent token is not validated')
            raise exceptions.AuthenticationFailed(msg)
        
        if validate_date:
            if validate_date <= datetime.datetime.now():
                msg = _('permanent token is not in validated date')
                raise exceptions.AuthenticationFailed(msg)
        
        User = get_user_model()
        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)
        
        permanent_token.update(lastest_success_date=datetime.datetime.now(), invoke_success_count=F('invoke_success_count')+1)

        return (user, token_value)


class TemporaryTokenAuthentication(BaseAuthentication):
    """
    临时token认证
    """
    def authenticate(self, request):
        auth_header_prefix='temp_token'
        token_value = get_token_value(request, auth_header_prefix=auth_header_prefix)
        
        if token_value is None:
            raise exceptions.AuthenticationFailed(_('temp token is not in request parameters'))

        token_value = str(token_value)
        token_info = cache.get(auth_header_prefix+'_'+token_value)
        if token_info:
            User = get_user_model()
            username = token_info.get('user')
            user = User.objects.get_by_natural_key(username)
            # user = User.objects.first() # 查询user表第一条记录，虚构一个认证对象
            return (user, None)
        else:
            raise exceptions.AuthenticationFailed(_('temp token [%(token_value)s] is not validated') % {'token_value':token_value})


def get_token_value(request, auth_header_prefix='permanent_token'):
    """
    要支持既可以从header获取token   Authorization: permanent_token 675ab0baa7f747813903e8b7dbd14de3
    也可以从请求参数获取token       md5 时间+大随机数
    优先从header取值
    """
    header = get_authorization_header(request)
    if isinstance(header, bytes):
        header = header.decode(HTTP_HEADER_ENCODING)

    auth = header.split()
      
    if auth and str(auth[0].lower()) != auth_header_prefix:
        return None

    if len(auth) == 1:
        msg = _('Invalid Authorization header. No credentials provided.')
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = _('Invalid Authorization header. Credentials string should not contain spaces.')
        raise exceptions.AuthenticationFailed(msg)
    
    # 从请求参数中获取
    if not auth:
        return request.GET.get(auth_header_prefix)
    
    return auth[1]


def request_params_check(invoke_rule_ids, request):
    """
    对请求的参数进行校验
    invoke_rule_ids        ApiInvokeRule.id 构成的数组，如 [1,3,5]
    """
    invoke_rules = ApiInvokeRule.objects.filter(id__in=invoke_rule_ids)
    
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        from_host = str(request.META['HTTP_X_FORWARDED_FOR'])
    else:
        from_host = str(request.META['REMOTE_ADDR'])
        
    _must_match_flag = []
    must_match_flag = False
    choice_match_flag = False
    for invoke_rule in invoke_rules:
        # 必须存在匹配项
        # '/api/v1/home/info', ['/api/v1/home/info'] 
        must_matchs = [(request.path, json.loads(invoke_rule.path.strip()   )  if invoke_rule.path and invoke_rule.path.strip()  else []  ),
                      (request.method,  json.loads(invoke_rule.method.strip() )  if invoke_rule.method and invoke_rule.method.strip() else []  ),
                      (from_host,  json.loads(invoke_rule.source.strip() )  if invoke_rule.source and invoke_rule.source.strip() else []  ),]
        
        # 如果key存在匹配，则值必须存在匹配项
        # 
        choice_matchs = [(request.GET, json.loads(invoke_rule.params.strip() )  if invoke_rule.params and invoke_rule.params.strip() else []  ),
                         (request.data, json.loads(invoke_rule.body.strip()   )  if invoke_rule.body and invoke_rule.body.strip()   else []  ),]             
        
        def must_match_check(must_match):
            # print(must_match[0], must_match[1],regexp_check(must_match[0], must_match[1]))
            return regexp_check(must_match[0], must_match[1])
        
        
        must_match_flag = all(map(must_match_check, must_matchs))
        _must_match_flag.append(must_match_flag)
        if must_match_flag:
            # 所有参数都要进行检查通过，即url参数和body值都要校验
            choice_match_flag = all(map(choice_match_check, choice_matchs))
            # must_match_flag choice_match_flag都为True，说明检查通过，不需要再校验下一条规则
            if choice_match_flag:
                break
        
    if not any(_must_match_flag):
        msg = _('no invoke rule match')
        raise exceptions.AuthenticationFailed(msg)
        
    if not choice_match_flag:
        msg = _('invoke url params not allow')
        raise exceptions.AuthenticationFailed(msg)



def regexp_check(request_params, regexps):
    """
    request_params        '/api/v1/home/info'
    regexps               ['/api/v1/home/info','/api/v2/.*']
    """
    for regexp in regexps:
        match_flag = re.match(regexp, request_params)
        if match_flag and match_flag.group() == request_params:
            return True
            
    return False


def choice_match_check(choice_match):
    """
    只要参数匹配一条规则即可通过
                   参数                        规则列表
    choice_match ( QueryDict('a=aaa&b=bbb'),  [{'a': 'aaaa', 'v': 'vvv'}] )
          or     ( {'a':'aaaa','b':'bbbb'},   [{'a': 'aaaa', 'v': 'vvv'}] )
    """
    request_pamas = choice_match[0]
    choice_match_rules = choice_match[1]
    def _choice_match_check(choice_match_rule):
        if isinstance(request_pamas,dict):
            _check = single_choice_rule_check_dict
        else:
            _check = single_choice_rule_check_querydict
        # print(request_pamas, choice_match_rules, _check(request_pamas, choice_match_rule))
        return _check(request_pamas, choice_match_rule)
    # 规则为空则视为匹配
    if not choice_match_rules:
        # print(request_pamas, choice_match_rules, True, "rule is empty")
        return True
    # 匹配一条规则即可
    return any(map(_choice_match_check, choice_match_rules))


def single_choice_rule_check_querydict(request_pamas, choice_match_rule):
    """
    key存在，则校验值；key不存在，则不校验；key都不存在，则通过
    request_pamas        QueryDict('a=aaaa&c=cccc')
    choice_match_rule    {'a':'aaaa','b':'bbbb'}
    """
    for k in request_pamas.keys():
        __choice_match_rule = choice_match_rule.get(k)
        if __choice_match_rule:
            sub_match_flag = False
            _choice_match_rule = [__choice_match_rule]
            for param_value in request_pamas.getlist(k):
                sub_match_flag = regexp_check(param_value, _choice_match_rule)
                # print(param_value,_choice_match_rule,sub_match_flag)
                # 一个key可能有多个值，要求所有值都匹配
            
            # 对于单条规则，如果匹配key，但key的值不匹配，则说明该规则不匹配
            if not sub_match_flag:
                return False
    
    return True


def single_choice_rule_check_dict(request_pamas, choice_match_rule):
    """
    与single_choice_rule_check_querydict类似，只是这里的参数为字典格式
    request_pamas        {'a':'aaaa','c':'cccc'}
    choice_match_rule    {'a':'aaaa','b':'bbbb'}
    """
    for k in request_pamas.keys():
        __choice_match_rule = choice_match_rule.get(k)
        if __choice_match_rule:
            sub_match_flag = False
            _choice_match_rule = [__choice_match_rule]
            # value值全部当成字符串处理
            param_value = str(request_pamas.get(k))
            sub_match_flag = regexp_check(param_value, _choice_match_rule)            
            # 对于单条规则，如果匹配key，但key的值不匹配，则说明该规则不匹配
            if not sub_match_flag:
                return False
    
    return True
