"""
Django DEVELOPMENT settings for RSEAdmin project.


For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ_DIR = os.path.join(BASE_DIR, 'RSEAdmin')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [
    'polymorphic',
    'rse.apps.RseConfig',
    'timetracking.apps.TimetrackingConfig', # The following line should be commented out to remove the time tracking application (before creating DB)
    'django_adminlte',
    'django_adminlte_theme',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'RSEAdmin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(PROJ_DIR, 'templates')),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # site wide template tags and filters
            'libraries': {
                'site_tags': 'RSEAdmin.templatetags.site_tags'
            },
        },
    },
]



WSGI_APPLICATION = 'RSEAdmin.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# authentication

LOGIN_URL =  'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

DATE_FORMAT = 'd/m/Y'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_I18N = True

# USE_L10N = True

USE_TZ = True

###############################################
# Time tracking application required settings #
###############################################

# Working hours per day (37 hour work week)
WORKING_HOURS_PER_DAY = 7.4

# 1.35 is 35% which is estimated (as 12% NI, 22.5% pension contribution and 0.5% appreticeship levy)
ONCOSTS_SALARY_MULTIPLIER = 1.35


###############################
# RSEAdmin required setttings #
###############################

# Working days per year (TRAC Days)
WORKING_DAYS_PER_YEAR = 220

# Number of items to show in lists such as starting soon
HOME_PAGE_NUMBER_ITEMS = 7

# Warning level for RSE capacity (in percent)
HOME_PAGE_RSE_MIN_CAPACITY_WARNING_LEVEL = 80

# Days to consider as soon
HOME_PAGE_DAYS_SOON = 365

# Days to consider as recent on home page
HOME_PAGE_DAYS_RECENT = 30

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
