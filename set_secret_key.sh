#!/bin/bash
#替换django配置文件的SECRET_KEY
#可以多次运行该脚本或者手动更改django配置文件

shellpath=$(cd "$(dirname "$0")";pwd)
cd ${shellpath}

PYTHON=python
config_file=setting/settings.py

SECRET_KEY=`$PYTHON -c "from django.core.management.utils import get_random_secret_key;print(get_random_secret_key())"`
ret=$?
#sed会特殊处理符号"&",因而先特殊处理成"\&"
#echo "SECRET_KEY = '"${SECRET_KEY}"'"
SECRET_KEY=`echo ${SECRET_KEY} | sed "s|&|\\\\\\&|g"`
#echo "SECRET_KEY = '"${SECRET_KEY}"'"
if [ $ret -eq 0 ];then
    sed -i "s|^SECRET_KEY.*|SECRET_KEY = '${SECRET_KEY}'|g" $config_file
    echo -e "replace ${config_file} SECRET_KEY \e[1;32m done \e[0m"
else
    echo -e "replace ${config_file} SECRET_KEY \e[1;31m failed \e[0m"
    exit 1
fi
