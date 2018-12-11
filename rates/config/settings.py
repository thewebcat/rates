import importlib
import os

C_PROJECT_STACK = os.environ.get('C_PROJECT_STACK', 'dev')

C_PROJECT_STACK_SETTINGS = importlib.import_module(
    f'rates.config.{C_PROJECT_STACK}'
)

for k in dir(C_PROJECT_STACK_SETTINGS):
    globals()[k] = C_PROJECT_STACK_SETTINGS.__dict__[k]
