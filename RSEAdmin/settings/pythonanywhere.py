"""
Django settings for Python Anywhere production server.

"""

from .base import *

import json
import os
from django.core.exceptions import ImproperlyConfigured

# Important secrets are stored in secrets file
with open(os.path.join(BASE_DIR, 'secrets.json')) as secrets_file:
    secrets = json.load(secrets_file)

def get_secret(setting, secrets=secrets):
    """Get secret setting or fail with ImproperlyConfigured"""
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured("Set the {} setting".format(setting))



# Sectret things from untracked sectrets file
PA_USER = get_secret('PA_USER')
SECRET_KEY = get_secret('SECRET_KEY')
DB_USER = get_secret('DB_USER')
DB_PASSWORD = get_secret('DB_PASSWORD')
DB_NAME = get_secret('DB_NAME')

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = True

# This should not be *
ALLOWED_HOSTS = [f'{PA_USER}.pythonanywhere.com']


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': f'{PA_USER}${DB_NAME}',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': f'{PA_USER}.mysql.pythonanywhere-services.com',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'static-root')
# Must match the Static files URL in PA Web tab
STATIC_URL = '/static/'

#Enable SSL redirects
SECURE_SSL_REDIRECT = True