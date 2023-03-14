import api_keys

import urllib
import requests
import json
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


def get_voice_url(message: dict) -> str:
    voice_id = message['voice']['file_id']
    debug(f'{voice_id = }')
    get_file_url = f'{TELEGRAM_BOT_API_PREFIX}' \
            f'{api_keys.TELEGRAM_BOT_TOKEN}/getfile?file_id={voice_id}'
    result = requests.get(get_file_url)
    voice_path = result.json()['result']['file_path']
    voice_url = f'https://api.telegram.org/file/bot' \
            f'{api_keys.TELEGRAM_BOT_TOKEN}/{voice_path}'
    return voice_url


def send_message(chat_id: int, message: str) -> None:
    info('start')
    if not chat_id or not message:
        info('finish')
        return

    message = urllib.parse.quote(message.encode('utf-8'))
    
    telegram_request_url = (
            f'{TELEGRAM_BOT_API_PREFIX}'
            f'{api_keys.TELEGRAM_BOT_TOKEN}'
            f'/sendMessage'
            f'?chat_id={chat_id}'
            f'&text={message}'
        )
    
    try:
        result = requests.post(telegram_request_url)
        logging.info(f'{telegram_request_url = }')
        if result.status_code != 200:
            logging.info(f'{telegram_request_url = }\n{result.text = }')
    except urllib.error.HTTPError as e:
        logging.info(f'HTTPError for url: {telegram_request_url}\n\nException: {e}')

    info('finish')