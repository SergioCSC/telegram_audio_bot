import config as cfg

from logging import info, debug
import io
import requests


HUGGING_FACE_MODEL_URL_PREFIX = 'https://api-inference.huggingface.co/models/'


def _post(url: str, headers: dict, data: bytes) -> tuple[requests.Response, dict]:
    response = requests.post(url, headers=headers, data=data)
    return response, response.json()


def audio2text(model: str, audio: bytes) -> tuple[str, int]:
    debug('start')
    headers = {'Authorization': f'Bearer {cfg.HUGGING_FACE_API_KEY}'}
    url = HUGGING_FACE_MODEL_URL_PREFIX + model
    response, returned_json = _post(url, headers, audio)
    text = str(returned_json.get('text', ''))
    error = str(returned_json.get('error', ''))
    
    if response.status_code == 503 \
            and ('is currently loading' in error
                 or 'Service Unavailable' in error):
        sleeping_time = int(returned_json.get('estimated_time', 20)) + 1
        return error, sleeping_time

    elif response.status_code == 500 \
            and 'Internal Server Error' in error:
        return error, -1
    # data = {'model': 'whisper-1', 'language': 'ru'}  # TODO get language from Telegram update language_code
    elif response.status_code == 200:
        if not text:
            text = 'Не смог найти слова в аудио, сорян'
        return text, -1
    else:
        text = f'Статус код ответа Hugging Face: {response.status_code}'
        if error:
            text = f'{text}\nСообщение об ошибке от Hugging Face: {error}'
    debug('finish')
    return text, -1


def downgrade(model: str) -> str:
    match model:
        case 'openai/whisper-large-v3':
            return 'openai/whisper-medium'
        case 'openai/whisper-medium':
            return 'openai/whisper-small'
        case 'openai/whisper-small':
            return 'openai/whisper-base'
        case 'openai/whisper-base':
            return 'openai/whisper-tiny'
        case 'openai/whisper-tiny':
            return 'openai/whisper-tiny'
        case _:
            return model

# output = query("sample1.flac")