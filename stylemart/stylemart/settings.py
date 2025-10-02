import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-@g&kf6a9^!z!l%w$#r4fqo0%y1r$c#%u)@5$#3*!+6y2!s#k$%'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'footer',
    'haystack',

]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.PerPathSessionMiddleware",   # replaces SessionMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Default session cookie (user site)
SESSION_COOKIE_NAME = "sessionid"

# Separate cookie for admin site
ADMIN_SESSION_COOKIE_NAME = "admin_sessionid"
USER_SESSION_COOKIE_NAME = "dashboard"



ROOT_URLCONF = 'stylemart.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.categories',
                'footer.context_processors.footer_sections',

            ],
        },
    },
]

WSGI_APPLICATION = 'stylemart.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# ================== LOGIN/LOGOUT SETTINGS ==================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'   # after login, go home
LOGOUT_REDIRECT_URL = '/'  # after logout, go home

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JazzCash Sandbox Settings
JAZZCASH_MERCHANT_ID = "MC347935"
JAZZCASH_PASSWORD = "2us96t5z3x"
JAZZCASH_INTEGRITY_SALT = "248bfec9z8"

# JazzCash Endpoints
JAZZCASH_BASE_URL = "https://sandbox.jazzcash.com.pk/CustomerPortal/TransactionManagement/MerchantForm/"

# Return URL (JazzCash will POST response here)
JAZZCASH_RETURN_URL = "http://127.0.0.1:8000/payment/jazzcash/return/"

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    },
}