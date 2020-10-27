#!/bin/bash
#
# export REDIS_HOST=127.0.0.1
# export REDIS_PORT=6379
# export REDIS_PASSWORD=my_redis_passwd
#
cd /data/solve-backend
sed -i "s|127.0.0.1|${REDIS_HOST}|g" ./deploy.conf
sed -i "s|6379|${REDIS_PORT}|g" ./deploy.conf
sed -i "s|my_redis_passwd|${REDIS_PASSWORD}|g" ./deploy.conf
python set_config.py   
python manage.py runserver 0.0.0.0:8000