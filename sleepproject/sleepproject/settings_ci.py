# sleepproject/settings_ci.py
from .settings import *
import tempfile
import os

# ===== БАЗА ДАННЫХ =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ===== ХРАНИЛИЩЕ ФАЙЛОВ =====
TEMP_DIR = tempfile.gettempdir()
MEDIA_ROOT = os.path.join(TEMP_DIR, 'test_media')
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ===== КЭШИРОВАНИЕ - ПЕРЕОПРЕДЕЛЯЕМ РАДИКАЛЬНО =====
# Удаляем django-redis полностью и используем встроенный локальный кэш
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache-location',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        }
    }
}

# ===== CELERY - СИНХРОННЫЙ РЕЖИМ =====
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# ===== УСКОРЕНИЕ ТЕСТОВ =====
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Отключаем миграции
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# ===== ОТКЛЮЧАЕМ РЕДИС-ЗАВИСИМЫЕ МОДУЛИ =====
# Убедитесь что эти переменные перезаписывают main settings
if 'django_redis' in INSTALLED_APPS or hasattr(settings, 'SESSION_ENGINE'):
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
