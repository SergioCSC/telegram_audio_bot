import sys
from os import environ
import logging

IN_LINUX = sys.platform == 'linux'

OPEN_AI_API_KEY = environ.get('OPEN_AI_API_KEY')
TELEGRAM_BOT_TOKEN = environ['TELEGRAM_BOT_TOKEN']
HUGGING_FACE_API_KEY = environ['HUGGING_FACE_API_KEY']

HUGGING_FACE_MODEL = environ.get('HUGGING_FACE_MODEL',
                                 'openai/whisper-large-v3')

HUGGING_FACE_SPACE = environ.get('HUGGING_FACE_SPACE', 
                                 'https://openai-whisper.hf.space')
                                 # 'https://sanchit-gandhi-whisper-jax-diarization.hf.space')
                              #  'https://huggingface.co/spaces/openai/whisper')
                              #  'abidlabs/whisper-large-v2')
                              #  'hf-audio/whisper-large-v3')


IN_AWS_LAMBDA = 'AWS_LAMBDA_RUNTIME_API' in environ

# if you want to set webhook
AWS_LAMBDA_API_GATEWAY_URL = environ.get('AWS_LAMBDA_API_GATEWAY_URL')

LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO')

MAX_MEDIA_SIZE = int(environ.get('MAX_MEDIA_SIZE', 15)) * 1024 * 1024  # 15 MB