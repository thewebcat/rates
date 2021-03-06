# flake8: noqa
import os


DEBUG = False
LOGGING_LEVEL = 'ERROR'
MODELS_PATTERN = '**/models.py'

BASE_DIR = os.path.abspath(os.getcwd())

LOGGERS = {}

DATABASE = {'user': 'postgres',
            'password': 'secret',
            'database': 'rates',
            'host': 'db'}

RATES_URL = 'https://ratesjson.fxcm.com/DataDisplayer'
