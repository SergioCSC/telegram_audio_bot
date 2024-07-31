import sys
from os import environ
import logging

IN_LINUX = sys.platform == 'linux'

OPEN_AI_API_KEY = environ['OPEN_AI_API_KEY']
TELEGRAM_BOT_TOKEN = environ['TELEGRAM_BOT_TOKEN']
IN_AWS_LAMBDA = 'AWS_LAMBDA_RUNTIME_API' in environ
AWS_LAMBDA_API_GATEWAY_URL = environ.get('AWS_LAMBDA_API_GATEWAY_URL')

LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO')