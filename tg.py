import config as cfg

import requests

import json
import urllib
import logging
from logging import info, debug


TELEGRAM_BOT_API_PREFIX = 'https://api.telegram.org/bot'


def get_update_message(event: dict) -> dict:
    if event.get('httpMethod') not in ('GET','POST'):  # event initiated by telegram
        return {}
    debug(f'{event = }')
    update = event.get('body')
    assert update
    update = json.loads(update)
    message = update.get('message', {})
    return message


def get_audio_url(message: dict) -> str:
    voice_id = message.get('voice', message.get('audio'))['file_id']
    debug(f'{voice_id = }')
    get_file_url = f'{TELEGRAM_BOT_API_PREFIX}' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/getfile?file_id={voice_id}'
    result = requests.get(get_file_url)
    voice_path = result.json()['result']['file_path']
    voice_url = f'https://api.telegram.org/file/bot' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/{voice_path}'
    return voice_url


def delete_webhook() -> None:
    delete_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        '/deletewebhook'
    requests.get(delete_webhook_url)
    

def set_webhook() -> None:
    set_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        f'/setwebhook?url={cfg.AWS_LAMBDA_API_GATEWAY_URL}' \
        f'&max_connections=2'
    requests.get(set_webhook_url)


def send_message(chat_id: int, message: str) -> None:
    info('start')
    if not chat_id or not message:
        info('finish')
        return

    message = urllib.parse.quote(message.encode('utf-8'))
    
    telegram_request_url = (
            f'{TELEGRAM_BOT_API_PREFIX}'
            f'{cfg.TELEGRAM_BOT_TOKEN}'
            f'/sendMessage'
            f'?chat_id={chat_id}'
            f'&text={message}'
        )
    
    try:
        result = requests.get(telegram_request_url)
        logging.info(f'{telegram_request_url = }')
        if result.status_code != 200:
            logging.info(f'{telegram_request_url = }\n{result.text = }')
    except urllib.error.HTTPError as e:
        logging.info(f'HTTPError for url: {telegram_request_url}\n\nException: {e}')

    info('finish')