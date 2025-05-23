#!/bin/bash
#
# export REDIS_HOST=127.0.0.1
# export REDIS_PORT=6379
# export REDIS_PASSWORD=my_redis_passwd
#
cd /data/solve-backend
sed -i "s|my_redis_passwd|${REDIS_PASSWORD}|g" ./deploy.conf
if [[ -n ${REDIS_HOST} ]]; then sed -i "s|'127.0.0.1'|'${REDIS_HOST}'|g" ./deploy.conf;fi
if [[ -n ${REDIS_PORT} ]]; then sed -i "s|6379|${REDIS_PORT}|g" ./deploy.conf;fi
if [[ -n ${MONGO_URI}  ]]; then sed -i "s|#uri=.*|uri=${MONGO_URI}|g" ./deploy.conf;fi
if [[ -n ${MONGO_DB}   ]]; then sed -i "s|#db=solve|db=${MONGO_DB}|g" ./deploy.conf;fi
if [[ -n ${DATA_PATH}  ]]; then sed -i "s|/tmp/|${DATA_PATH}|g" ./deploy.conf;fi
if [[ -n ${SECRET_KEY} ]]; then 
SECRET_KEY=`echo ${SECRET_KEY} | sed "s|&|\\\\\\&|g"` \
&& sed -i "s|^SECRET_KEY.*|SECRET_KEY = '${SECRET_KEY}'|g"  ./setting/settings.py
fi
python set_config.py   
nohup python durable_server.py &
python manage.py runserver 0.0.0.0:8000