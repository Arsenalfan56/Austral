"""
Django settings for erp_austral project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ===== SEGURIDAD Y VARIABLES DE ENTORNO =====
# En Render leerá esto de las variables de entorno. En tu PC usará el texto por defecto.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-mrm)l-f_685nvp&3ze5i2g^0bjzzc(%-z^ap-m=kin8^k+zmfd')

# En Render será False (porque lo configuraremos así). En tu PC será True.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Permite todos los hosts (útil para Render y para probar en la oficina)
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin', # <--- Tema visual agregado aquí, justo antes de admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'logistica',
    'costos',
    'proyectos',
    'Mejoramiento',
    'bi',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # WhiteNoise justo después de Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_austral.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.debug',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_austral.wsgi.application'


# ===== CONFIGURACIÓN DE BASE DE DATOS HÍBRIDA =====
# Si estás en Render (existe DATABASE_URL), usa PostgreSQL.
# Si estás en tu PC (no existe DATABASE_URL), usa SQLite local.
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True


# ===== ARCHIVOS ESTÁTICOS Y MULTIMEDIA (WHITENOISE) =====
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ¡ATENCIÓN! Django 5+ usa esta nueva configuración (STORAGES) en lugar de STATICFILES_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===== CONFIGURACIÓN DE LOGIN =====
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'


# ===== CONFIGURACIÓN DE SESIÓN =====
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 300 # 300 segundos = 5 minutos
SESSION_SAVE_EVERY_REQUEST = True


# ==========================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO (GMAIL)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# En Render leerá las variables de entorno, en tu PC usará los valores por defecto
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '09racl@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'rzlt rewd tact yatl')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Austral V&T ERP <09racl@gmail.com>')

# ===== FORZAR MODO CLARO EN EL ADMIN =====
# Esto desactiva la detección automática de modo oscuro del sistema operativo
