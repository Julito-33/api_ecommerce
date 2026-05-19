# ─────────────────────────────────────────────────────────────────────────────
# settings.py
#
# Configuración central de Django.
# Aquí se define todo: base de datos, apps instaladas, JWT, Redis, CORS, etc.
# Las credenciales sensibles vienen del archivo .env, nunca hardcodeadas aquí.
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from decouple import config
from datetime import timedelta

# Ruta base del proyecto — todos los paths se construyen desde aquí
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Seguridad
# ─────────────────────────────────────────────────────────────────────────────

# Clave secreta de Django — viene del .env, nunca la expongas
SECRET_KEY = config('SECRET_KEY')

# En producción esto debe ser False
DEBUG = config('DEBUG', default=True, cast=bool)

# En producción agregar el dominio real: ['tiendanaranja.com.py']
ALLOWED_HOSTS = ['*']

# ─────────────────────────────────────────────────────────────────────────────
# Aplicaciones instaladas
# Aquí registramos Django, las librerías y nuestras propias apps
# ─────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías instaladas
    'rest_framework',            # Django REST Framework — para construir la API
    'rest_framework_simplejwt',  # Autenticación con JWT
    'corsheaders',               # Permite que el frontend llame a esta API

    # Nuestras apps
    'apps.users',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.payments',
    'apps.reviews',
    'apps.invoices',
]

# ─────────────────────────────────────────────────────────────────────────────
# Middlewares — se ejecutan en cada request antes de llegar a las vistas
# ─────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',        # CORS va antes que CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tienda_naranja.urls'

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

WSGI_APPLICATION = 'tienda_naranja.wsgi.application'

# ─────────────────────────────────────────────────────────────────────────────
# Base de datos — PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Redis — para el carrito y caché
# ─────────────────────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Django REST Framework — configuración global de la API
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Por defecto todos los endpoints requieren autenticación
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Paginación automática en todos los listados
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─────────────────────────────────────────────────────────────────────────────
# JWT — configuración de tokens
# ─────────────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─────────────────────────────────────────────────────────────────────────────
# CORS — permite que el frontend React llame a esta API
# ─────────────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',   # Frontend React en desarrollo
    'http://localhost:3000',
]

# ─────────────────────────────────────────────────────────────────────────────
# Modelo de usuario personalizado
# Le decimos a Django que use nuestro modelo en vez del suyo por defecto
# ─────────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

# ─────────────────────────────────────────────────────────────────────────────
# Archivos estáticos y media (imágenes de productos)
# ─────────────────────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# Zona horaria — Paraguay
TIME_ZONE = 'America/Asuncion'
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────────────────────
# Stripe y MercadoPago
# ─────────────────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY        = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET    = config('STRIPE_WEBHOOK_SECRET', default='')
MERCADOPAGO_ACCESS_TOKEN = config('MERCADOPAGO_ACCESS_TOKEN', default='')