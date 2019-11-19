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

