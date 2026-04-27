# -*- coding: utf-8 -*-
from auth_new.models import Account, PermanentToken, ApiInvokeRule
from rest_framework import serializers


class UserINFO(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Account
        fields = ("id", "username")


class PermanentTokenINFO(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PermanentToken
        fields = (
            "id",
            "token",
            "username",
            "expire_date",
            "create_date",
            "lastest_date",
            "invoke_count",
            "invoke_success_count",
            "lastest_success_date",
            "max_invoke",
            "invoke_rule_ids",
            "is_validate",
        )


class ApiInvokeRuleINFO(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ApiInvokeRule
        fields = ("id", "source", "method", "params", "body", "path")
