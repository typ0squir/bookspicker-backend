import environ
from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()

# SECURITY WARNING: keep the secret key used in production secret!
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = []

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# Application definition

INSTALLED_APPS = [
    # local apps
    'accounts',
    'api',

    # 3rd party
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # allauth 관련
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # django 기본
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookspicker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookspicker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'


SITE_ID = 1 # 어떤 도메인에서 OAuth를 처리할지
# Django의 django.contrib.sites 프레임워크에서 “현재 사용 중인 사이트는 ID=1번 사이트다”라는 뜻.
# 1. 구글 콘솔에서 redirect URI를 http://127.0.0.1:8000/accounts/google/login/callback/ 로 등록
# 2. Django admin → Sites 테이블에서 Domain을 127.0.0.1:8000 로 설정
# 3. SocialApp(Google OAuth)과 Sites(1번) 을 연결함
# 4. allauth는 SITE_ID를 기준으로 “지금 이 로그인은 사이트 1번에서 발생한 요청이다”라고 이해
# -> 즉, SITE_ID는 OAuth가 정확한 redirect-domain 매칭을 하게 해주는 필수 키다.

AUTHENTICATION_BACKENDS = [ # Django에게 “로그인을 처리할 때 어떤 인증 방식을 사용할지” 알려주는 리스트.
    'django.contrib.auth.backends.ModelBackend',               # 기본 로그인 방식(admin 로그인 때 필요)
    'allauth.account.auth_backends.AuthenticationBackend',     # allauth
]


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_EMAIL_VERIFICATION = "none" # 회원가입 후 이메일 인증 과정을 생략.
ACCOUNT_LOGIN_METHODS = {"username"}    # 로그인 시 어떤 방식으로 인증할지 지정
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"

ACCOUNT_SIGNUP_FIELDS = [   # 회원가입 폼에 어떤 필드를 받을지 지정
    "email*",
    "username*",
    "password1*",
    "password2*",
]


# settings.py
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID"),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET"),
            "key": ""
        }
    }
}

GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT_URI = env("GOOGLE_OAUTH_REDIRECT_URI")

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

SIMPLE_JWT = {
    # 예: 5분 → 4시간
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),

    # 필요하면 refresh 토큰도 같이
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),

    # Authorization: Bearer <token>
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


