#!/bin/bash
#
# export REDIS_HOST=127.0.0.1
# export REDIS_PORT=6379
# export REDIS_PASSWORD=my_redis_passwd
#
cd /data/solve-backend
sed -i "s|my_redis_passwd|${REDIS_PASSWORD}|g" ./deploy.conf
if [ "X${REDIS_HOST}X" != "XX" ]; then sed -i "s|host=127.0.0.1|host=${REDIS_HOST}|g" ./deploy.conf;fi
if [ "X${REDIS_PORT}X" != "XX" ]; then sed -i "s|6379|${REDIS_PORT}|g" ./deploy.conf;fi
if [ "X${SECRET_KEY}X" != "XX" ]; then 
SECRET_KEY=`echo ${SECRET_KEY} | sed "s|&|\\\\\\&|g"` \
&& sed -i "s|^SECRET_KEY.*|SECRET_KEY = '${SECRET_KEY}'|g"  ./setting/settings.py
fi
python set_config.py   
python manage.py runserver 0.0.0.0:8000