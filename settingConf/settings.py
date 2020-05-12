#coding:utf8
"""
Django settings for auto_deploy project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
import os
import datetime


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yjs)1t@pw$02_ja@*pxg2a$*i_5z=kaucx1$!qtj92^oemh*pi'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'auth_new.Account'

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'rest_framework',
    'auth_new.apps.AuthNewConfig',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
]
CORS_ORIGIN_ALLOW_ALL = True
CSRF_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'POST',
    'PUT',
)

ROOT_URLCONF = 'settingConf.urls'

WSGI_APPLICATION = 'settingConf.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'dbname',
#        'USER': 'dbuser',
#        "PORT": 3306,
#        "PASSWORD": 'dbpasswd',
#        "HOST": '127.0.0.1'
#    }
#}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    #访问频率设置  ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')
    'DEFAULT_THROTTLE_RATES': {
        'anylogin': '10/m'
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #用于浏览器展示
        'DIRS': 'rest_framework/Templates',    
        'APP_DIRS': True,
        #'OPTIONS': {
        #    'context_processors': [
        #        'django.template.context_processors.debug',
        #        'django.template.context_processors.request',
        #        'django.contrib.auth.context_processors.auth',
        #        'django.contrib.messages.context_processors.messages',
        #    ],
        #},
    },
]

JWT_AUTH = {
    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_response_payload_handler',
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=86400),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s] - %(message)s'},
        'simple': {
            'format': '%(asctime)s - %(message)s'}
    },
    'filters': {
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'standard'
        },
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/info.log',      # 日志输出文件
            'maxBytes': 1024 * 1024 * 10,     # 文件大小
            'backupCount': 100,               # 备份份数
            'formatter': 'simple',            # 日志格式
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.request': {
            'handlers': ['error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'solve.core.views': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }

    }
}

##############

# 用于auth_new模块
# 使用CAS
# if don't use, set: CAS_URL=''
CAS_URL='http://192.168.253.128:9095/cas'
#CAS_URL=''
"""
CAS协议提供的接口：
login                #登陆(前端使用)
logout               #登出(前端使用)
validate             #验证ticket 返回text格式 (后端使用)
serviceValidate      #验证ticket 返回xml格式  (后端使用)
"""

# 用于auth_new模块
# 用于接口函数错误捕获的装饰器  
ERROR_CAPTURE='libs.wrapper.error_capture'
#ERROR_CAPTURE=''



##################
# 用于持久保存redis的数据
# 如果不设置，则数据全部存在redis中，过期则清除
#可以设置为{}或者全部清除
#MONGODB_CONFIG = {}
MONGODB_CONFIG = {
    'host': '127.0.0.1',
    'port': 27017,
    'db': 'solve',
    'user': 'solve',
    'passwd': 'solve123456'

}
