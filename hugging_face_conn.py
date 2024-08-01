import config as cfg

from logging import info, debug
import io
import requests
from time import sleep


HUGGING_FACE_MODEL_URL_PREFIX = 'https://api-inference.huggingface.co/models/'


def _post(url: str, headers: dict, data: bytes) -> tuple[requests.Response, dict]:
    response = requests.post(url, headers=headers, data=data)
    return response, response.json()


def audio2text(audio: bytes) -> str:
    debug('start')
    headers = {'Authorization': f'Bearer {cfg.HUGGING_FACE_API_KEY}'}
    url = HUGGING_FACE_MODEL_URL_PREFIX + cfg.HUGGING_FACE_MODEL
    response, returned_json = _post(url, headers, audio)
    while response.status_code == 503 and 'is currently loading' in returned_json.get('error', ''):
        # resubmit
        sleeping_time = int(returned_json.get('estimated_time', 20)) + 1
        debug_text = f'Hugging face asked to wait for {sleeping_time} s. Sleeping ...'
        debug(debug_text)
        sleep(sleeping_time)
        response, returned_json = _post(url, headers, audio)

    # data = {'model': 'whisper-1', 'language': 'ru'}  # TODO get language from Telegram update language_code
    if response.status_code == 200:
        text = returned_json.get('text')
        if not text:
            text = 'Не смог найти слова в аудио, сорян'
    else:
        text = f'Статус код ответа Hugging Face: {response.status_code}'
        if error_text := str(returned_json.get('error', {})):
            text = f'{text}\nСообщение об ошибке от Hugging Face: {error_text}'
    debug('finish')
    return f'Hugging face responce:        \
            \n{text}'

# output = query("sample1.flac")