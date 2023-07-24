"""
Django settings for RSEAdmin project DEV.

"""
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')-x8s!s6jxz2(^ni8i&7xv!dcz+ov^q26psdlt89n1%c#k_v6!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DEV_CONTAINER = os.getenv('DEV_CONTAINER')

# Use Postgres with containers
if DEV_CONTAINER is not None:
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'django')
    
    DATABASES = dict(
        default={
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_NAME,
            'USER': os.getenv('DATABASE_USER', 'django'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', 'django_postgres'),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': int(os.getenv('DATABASE_PORT', '5432')),
            # Test database
            # https://docs.djangoproject.com/en/4.0/topics/testing/overview/#the-test-database
            # https://docs.djangoproject.com/en/4.0/ref/settings/#test
            'TEST': {
                'NAME': f"test_{DATABASE_NAME}",
            }
        }
    )
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static-root/')

