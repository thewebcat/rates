# flake8: noqa
from .default import *

from logging import config as logging_config

DEBUG = True

LOGGING_LEVEL = 'DEBUG'

LOG_DIR = ''

LOGGERS.update({
    '': {
        'handlers': ['console', 'debug_handler', 'error_handler'] if LOG_DIR else ['console'],
        'level': LOGGING_LEVEL,
    }
})

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(name)s [%(asctime)s] %(filename)s:%(lineno)s %(message)s',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z',
            'fmt': '%(levelname)s %(name)s [%(asctime)s] %(pathname)s %(lineno)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        },
        'debug_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'json',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
        },
        'error_handler': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'formatter': 'json',
            'filename': os.path.join(LOG_DIR, 'error.log'),
        },
    },
    'loggers': LOGGERS
}

logging_config.dictConfig(LOGGING)
