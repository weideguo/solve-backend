#!/bin/bash
#生产django配置文件的SECRET_KEY

shellpath=$(cd "$(dirname "$0")";pwd)
cd ${shellpath}

PYTHON=python


$PYTHON -c "from django.core.management.utils import get_random_secret_key;print(get_random_secret_key())"

