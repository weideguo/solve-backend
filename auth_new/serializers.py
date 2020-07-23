# -*- coding: utf-8 -*- 
from auth_new.models import Account
from rest_framework import serializers



class UserINFO(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Account
        fields = ('id', 'username')
