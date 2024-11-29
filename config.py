import sys
from os import environ
import logging

IN_LINUX = sys.platform == 'linux'

OPEN_AI_API_KEY = environ.get('OPEN_AI_API_KEY')
TELEGRAM_BOT_TOKEN = environ['TELEGRAM_BOT_TOKEN']
HUGGING_FACE_API_KEY = environ['HUGGING_FACE_API_KEY']
DEEPGRAM_API_KEY = environ.get('DEEPGRAM_API_KEY')
GEMINI_API_KEY = environ.get('GEMINI_API_KEY')

HUGGING_FACE_MODEL = environ.get('HUGGING_FACE_MODEL',
                                 'openai/whisper-large-v3')

# HUGGING_FACE_TEXT_MODEL = environ.get('HUGGING_FACE_TEXT_MODEL',
#                                       'facebook/bart-large-cnn'
#                                     #  'mistralai/Mistral-7B-Instruct-v0.2') -- didn't try
#                                     # 'meta-llama/Llama-3.2-3B'
#                                     #  'meta-llama/Llama-3.1-8B' -- too big (16gb > 10gb)
#                            )

DEEPGRAM_MODEL = environ.get('DEEPGRAM_MODEL', 'whisper-large')

GEMINI_MODEL = environ.get('GEMINI_MODEL', 'gemini-1.5-flash')

HUGGING_FACE_SPACE = environ.get('HUGGING_FACE_SPACE',
                                 # 'nlogn/openai-whisper-small')
                                 # 'nlogn/openai-whisper-large-v3')
                                 'https://openai-whisper.hf.space')
                                 # 'https://sanchit-gandhi-whisper-jax-diarization.hf.space')
                              #  'https://huggingface.co/spaces/openai/whisper')
                              #  'abidlabs/whisper-large-v2')
                              # 'https://abidlabs-whisper-large-v2.hf.space/')
                              #  'hf-audio/whisper-large-v3')


IN_AWS_LAMBDA = 'AWS_LAMBDA_RUNTIME_API' in environ

# if you want to set webhook
AWS_LAMBDA_API_GATEWAY_URL = environ.get('AWS_LAMBDA_API_GATEWAY_URL')

LOG_LEVEL = environ.get('LOG_LEVEL', 'WARNING')

MAX_MEDIA_SIZE = int(environ.get('MAX_MEDIA_SIZE', 20)) * 1024 * 1024  # 20 MB
TEXT_LENGTH_TO_SUMMARIZE = int(environ.get('TEXT_LENGTH_TO_SUMMARIZE', 4000))

PERMITTED_TG_CHAT_USERNAMES = environ.get('PERMITTED_TG_CHAT_USERNAMES', '').split(',')
PERMITTED_TG_CHAT_USERNAMES = [username.strip() for username in PERMITTED_TG_CHAT_USERNAMES if username.strip()]