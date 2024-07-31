import sys
from os import environ
import logging

IN_LINUX = sys.platform == 'linux'

OPEN_AI_API_KEY = environ.get('OPEN_AI_API_KEY')
TELEGRAM_BOT_TOKEN = environ['TELEGRAM_BOT_TOKEN']
HUGGING_FACE_API_KEY = environ['HUGGING_FACE_API_KEY']

HUGGING_FACE_OPENAI_WHISPER_MODEL = environ.get('HUGGING_FACE_OPENAI_WHISPER_MODEL',
                                                'whisper-tiny')


IN_AWS_LAMBDA = 'AWS_LAMBDA_RUNTIME_API' in environ

# if you want to set webhook
AWS_LAMBDA_API_GATEWAY_URL = environ.get('AWS_LAMBDA_API_GATEWAY_URL')

LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO')