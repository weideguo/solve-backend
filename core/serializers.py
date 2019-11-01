#coding:utf8
from core.models import Account
from rest_framework import serializers



class UserINFO(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Account
        fields = ('id', 'username')
