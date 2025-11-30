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

# ===== КЭШИРОВАНИЕ =====
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

# ===== СЕССИИ =====
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ===== УСКОРЕНИЕ ТЕСТОВ =====
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ===== ПРАВИЛЬНОЕ ОТКЛЮЧЕНИЕ МИГРАЦИЙ =====
class DisableMigrations(dict):
    """Dict-like object that disables migrations"""
    def __missing__(self, key):
        return None

MIGRATION_MODULES = DisableMigrations()

# ===== ОТКЛЮЧАЕМ ЛОГИРОВАНИЕ В ТЕСТАХ =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# ===== ОТКЛЮЧАЕМ DEBUG_TOOLBAR ПОЛНОСТЬЮ =====
DEBUG = False
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda r: False,
}
