"""
Django settings for Shop_DJ project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import django_stubs_ext

django_stubs_ext.monkeypatch()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-19uq@+ebw9xhhhh^g!)%=v%7vl#m53pb_22pyj@&8e^4(9z27@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition
SITE_ID = 1

MIDDLEWARE = [
    # 'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
INSTALLED_APPS = [
    # 'django.contrib.sites',
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mptt',
    # 'django_json_widget',
    'django_summernote',
    'nested_admin',
    'adminsortable2',
    # 'django_telethon_session',
    'djmoney',
    'sorl.thumbnail',
    # 'django.contrib.redirects',
    'ROOTAPP',
    'catalog',
    'finance',
    'main_page',
    'baton.autodiscover',
    'django_svg_image_form_field',
    'solo',
    'site_settings',
    'phonenumber_field',
    'babel'
]

ROOT_URLCONF = 'Shop_DJ.urls'
# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATE_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR, ],
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

WSGI_APPLICATION = 'Shop_DJ.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'shop_dj_db',
        'USER': 'shop_dj_admin',
        'PASSWORD': '7898',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Kiev'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = 'media/'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # '0.0.0.0:8000'
    # ...
]
X_FRAME_OPTIONS = 'SAMEORIGIN'

BATON = {
    'SITE_HEADER': 'Baton',
    'SITE_TITLE': 'Baton',
    'INDEX_TITLE': 'Site administration',
    'SUPPORT_HREF': 'https://github.com/otto-torino/django-baton/issues',
    'COPYRIGHT': 'copyright © 2020 <a href="https://www.otto.to.it">Otto srl</a>',  # noqa
    'POWERED_BY': '<a href="https://www.otto.to.it">Otto srl</a>',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': False,
    'CHANGELIST_FILTERS_FORM': True,
    'MENU_ALWAYS_COLLAPSED': False,
    'MENU_TITLE': 'Приложения сайта',
    'MESSAGES_TOASTS': False,
    'GRAVATAR_DEFAULT_IMG': 'https://ru.gravatar.com/userimage/223686757/923cc17186456a164107fc1f0eb66dca.png',
    'LOGIN_SPLASH': '/static/core/img/byrka.jpg',
    'SEARCH_FIELD': {
        'label': 'Search contents...',
        'url': '/search/',
    },
    'MENU': (
        {
            'type': 'app',
            'name': 'auth',
            'label': 'Учетные записи админки',
            'icon': 'fa fa-lock',
            # 'default_open': True,
            'models': (
                {
                    'name': 'user',
                    'label': 'Users'
                },
                {
                    'name': 'group',
                    'label': 'Groups'
                },
            )
        },

        {
            'type': 'app',
            'name': 'main_page',
            'label': 'Главная страница',
            'icon': 'fa fa-home',
            'default_open': True,
            'models': (
                {
                    'name': 'menu',
                    'label': 'Конструктор меню'
                },
                {
                    'name': 'staticpage',
                    'label': 'Текстовые страницы'
                },
                {
                    'name': 'banner',
                    'label': 'Баннер'
                },
                {
                    'name': 'popularcategory',
                    'label': 'Актуальные категории'
                },
                {
                    'name': 'popularproduct',
                    'label': 'Популярные товары'
                },
                {
                    'name': 'newproduct',
                    'label': 'Новые поступления'
                },
            )
        },

        {
            'type': 'app',
            'name': 'catalog',
            'label': 'Товары и их основные свойства',
            'icon': 'fa fa-plug',
            'default_open': True,
            'models': (
                {
                    'name': 'product',
                    'label': 'Товары'
                },
                {
                    'name': 'country',
                    'label': 'Страны'
                },
                {
                    'name': 'brand',
                    'label': 'Бренды'
                },
                {
                    'name': 'productseries',
                    'label': 'Линейки товаров'
                },

            )
        },
        {
            'type': 'app',
            'name': 'catalog',
            'label': 'Категории и расширенные характеристики',
            'icon': 'fa fa-sitemap',
            'default_open': True,
            'models': (
                {
                    'name': 'category',
                    'label': 'Категории товаров'
                },
                {
                    'name': 'group',
                    'label': 'Группы атрибутов'
                },
                {
                    'name': 'attribute',
                    'label': 'Атрибуты'
                },

                {
                    'name': 'unitofmeasure',
                    'label': 'Еденицы измерения'
                },
                {
                    'name': 'combinationofcategory',
                    'label': 'Сочетания категорий'
                },

            )
        },

    ),
}
# PHONENUMBER_DEFAULT_REGION = 'UA'
# PHONENUMBER_DB_FORMAT = 'NATIONAL'
# PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'
