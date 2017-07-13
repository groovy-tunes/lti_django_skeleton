import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#LTI Configurations

# Configure PyLTI oauth settings
# PYLTI_CONFIG = {
#     "consumers": {
#         secrets["CONSUMER_KEY"]: {
#             "secret": secrets["CONSUMER_KEY_SECRET"],
#             "cert": secrets["CONSUMER_KEY_PEM_FILE"]
#         }
#     }
# }

# Configure server oauth settings
# SERVER_CERTIFICATE_FILE = secrets['SERVER_CERTIFICATE_FILE']
# SERVER_KEY_FILE = secrets['SERVER_KEY_FILE']

BLOCKLY_LOG_DIR = os.path.join(BASE_DIR, 'logs')

#configured for GMAIL
# MAIL_SERVER = 'smtp.gmail.com'
# MAIL_PORT = 465
# MAIL_USE_SSL = True
# # TODO: e.g., vt.blockpy@gmail.com
# MAIL_USERNAME = 'your_account@gmail.com'
# MAIL_PASSWORD = secrets.get("EMAIL_PASSWORD")
# # TODO: e.g., "BlockPy Admin"
# DEFAULT_MAIL_SENDER = 'Name of the email sender'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ee4oz8)m+m#(2@9ty5(z+d_z%yerositper(41xm6rhnaq12qe'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ltilaunch',
    'lti_django_skeleton',
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

AUTHENTICATION_BACKENDS = [
    'ltilaunch.auth.LTILaunchBackend',
    'django.contrib.auth.backends.ModelBackend'
]

ROOT_URLCONF = 'dev_skeleton.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dev_skeleton.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ltidev',
        'USER': 'ltidev',
        'PASSWORD': '',
        'HOST': 'localhost',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                               # Set to empty string for default.
    }
}


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


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = ''
STATIC_URL = '/static/'
