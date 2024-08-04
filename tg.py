import config as cfg

import requests

import json
import urllib
import logging
from logging import info, debug


TELEGRAM_BOT_API_PREFIX = 'https://api.telegram.org/bot'


def get_update_message(event: dict) -> dict:
    if http_method := event.get('httpMethod') not in ('GET','POST'):  # event initiated by telegram
        event_json = json.dumps(event)
        body_json = json.dumps(event.get('body'))
        logging.info(f'not GET or POST. Instead,  \
                     \n\n{http_method = },         \
                     \n\n{event_json = },         \
                     \n\n{body_json = }.          \
                     \n\nFinish')
        return {}
    update = event.get('body')
    assert update
    update = json.loads(update)
    message = update.get('message', {})
    if not message:
        logging.info('update is not a message. Look for edited_message')
        message = update.get('edited_message', {})
        if not message:
            logging.info('has no edited_message in update. Finish')
            return {}
    return message


def send_message(chat_id: int, message: str) -> None:
    debug('start')
    if not chat_id or not message:
        info('not chat id or not message. Finish')
        return

    messages = [message[i: i + 4000] for i in range(0, len(message), 4000)]
        
    for message in messages:

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
            debug(f'{telegram_request_url = }')
            if result.status_code != 200:
                info(f'{result.status_code = } \
                        \n{telegram_request_url = } \
                        \n{result.text = }')
        except urllib.error.HTTPError as e:
            info(f'HTTPError for url: {telegram_request_url} \
                    \n\nException: {e}')

    debug('finish')


def get_media_url(message: dict) -> str:
    media_id = message.get('voice', message.get('audio',
            message.get('video', message.get('video_note', 
            message.get('document')))))['file_id']
    debug(f'{media_id = }')
    get_file_url = f'{TELEGRAM_BOT_API_PREFIX}' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/getfile?file_id={media_id}'
    result = requests.get(get_file_url)
    media_path = result.json()['result']['file_path']
    media_url = f'https://api.telegram.org/file/bot' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/{media_path}'
    return media_url


def delete_webhook() -> None:
    delete_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        '/deletewebhook'
    requests.get(delete_webhook_url)


def set_webhook() -> None:
    allowed_updates = ['message', 'edited_message']
    allowed_updates_jsons = json.dumps(allowed_updates)
    set_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        f'/setwebhook?url={cfg.AWS_LAMBDA_API_GATEWAY_URL}' \
        f'&max_connections=2' \
        f'&allowed_updates={allowed_updates_jsons}' \

    requests.get(set_webhook_url)
