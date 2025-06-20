import sys
from os import environ
import logging

IN_LINUX = sys.platform == 'linux'

OPEN_AI_API_KEY = environ.get('OPEN_AI_API_KEY')
TELEGRAM_BOT_TOKEN = environ['TELEGRAM_BOT_TOKEN']
HUGGING_FACE_API_KEY = environ.get('HUGGING_FACE_API_KEY')
DEEPGRAM_API_KEY = environ.get('DEEPGRAM_API_KEY')
GROQ_API_KEY = environ.get('GROQ_API_KEY')
GEMINI_API_KEY = environ.get('GEMINI_API_KEY')

HUGGING_FACE_MODEL = environ.get('HUGGING_FACE_MODEL',
                                 'openai/whisper-large-v3')

# HUGGING_FACE_TEXT_MODEL = environ.get('HUGGING_FACE_TEXT_MODEL',
#                                       'facebook/bart-large-cnn'
#                                     #  'mistralai/Mistral-7B-Instruct-v0.2') -- didn't try
#                                     # 'meta-llama/Llama-3.2-3B'
#                                     #  'meta-llama/Llama-3.1-8B' -- too big (16gb > 10gb)
#                            )

GROQ_MODEL = environ.get('GROQ_MODEL', 'whisper-large-v3-turbo')
DEEPGRAM_MODEL = environ.get('DEEPGRAM_MODEL', 'whisper-large')

GEMINI_1ST_MODEL = environ.get('GEMINI_1ST_MODEL', 'gemini-2.5-flash-lite-preview-06-17')
GEMINI_2ND_MODEL = environ.get('GEMINI_2ND_MODEL', 'gemini-2.0-flash-lite')

GEMINI_YOUTUBE_MODEL_1ST_MODEL = environ.get('GEMINI_YOUTUBE_MODEL_1ST_MODEL', 'gemini-2.5-flash-lite-preview-06-17')
GEMINI_YOUTUBE_MODEL_2ND_MODEL = environ.get('GEMINI_YOUTUBE_MODEL_2ND_MODEL', 'gemini-2.5-flash-preview-05-20')


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
MIN_TEXT_LENGTH_TO_SUMMARIZE = int(environ.get('MIN_TEXT_LENGTH_TO_SUMMARIZE', 4000))
FRAMES_TO_ANALYZE = int(environ.get('FRAMES_TO_ANALYZE', 2))  # number of frames to analyze in video

PERMITTED_TG_CHAT_USERNAMES = environ.get('PERMITTED_TG_CHAT_USERNAMES', '').split(',')
PERMITTED_TG_CHAT_USERNAMES = [username.strip() for username in PERMITTED_TG_CHAT_USERNAMES if username.strip()]

YOUTUBE_CFG_NONAME = ''