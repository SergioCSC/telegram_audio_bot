import config as cfg

import requests

import json
import urllib
import tempfile
import logging
from logging import error, info, warning, debug


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
        error(f'Something is empty: {chat_id =}  {message = }. Finish')
        return

    messages = [message[i: i + 4000] for i in range(0, len(message), 4000)]
        
    for message in messages:

        message = urllib.parse.quote(message.encode('utf-8'))
    
        telegram_request_url = (
                f'{TELEGRAM_BOT_API_PREFIX}'
                f'{cfg.TELEGRAM_BOT_TOKEN}'
                f'/sendMessage'
                f'?chat_id={chat_id}'
                # f'&parse_mode=Markdown'
                f'&text={message}'
            )
    
        try:
            result = requests.get(telegram_request_url)
            debug(f'{telegram_request_url = }')
            if result.status_code != 200:
                error(f'{result.status_code = } \
                        \n{telegram_request_url = } \
                        \n{result.text = } \
                        \n{message = }')
        except urllib.error.HTTPError as e:
            error(f'HTTPError for url: {telegram_request_url} \
                    \n\nException: {e}')

    debug('finish')


def send_doc(chat_id: int, content_marker: str, text: str) -> None:
    debug('start')
    if not chat_id or not text:
        error(f'Something is empty: {chat_id =} {text = }. Finish')
        return

    telegram_request_url = (
            f'{TELEGRAM_BOT_API_PREFIX}'
            f'{cfg.TELEGRAM_BOT_TOKEN}'
            f'/sendDocument'
            f'?chat_id={chat_id}'
            # f'&parse_mode=Markdown'
            # f'&caption={summary}'
        )
    filename = content_marker + '.txt'
    files = {"document": (filename, text, "text/plain")}
    
    try:
        result = requests.post(telegram_request_url, files=files)
        debug(f'{telegram_request_url = }')
        if result.status_code != 200:
            error_message = f'{result.status_code = }' \
                            f'\n{telegram_request_url = }' \
                            f'\n{result.text = }' \
                            f'\n{text = }'
            error(error_message)
            send_message(chat_id, error_message)

    except urllib.error.HTTPError as e:
        info(f'HTTPError for url: {telegram_request_url} \
                \n\nException: {e}')

    debug('finish')


def get_media_url_and_size(message: dict, chat_id_to_send_error: int) -> tuple[str, int]:
    media_id = message.get('voice', message.get('audio',
            message.get('video', message.get('video_note', 
            message.get('document', 
            message.get('photo', [{'file_id':''}])[-1])))))['file_id']
    debug(f'{media_id = }')
    get_file_url = f'{TELEGRAM_BOT_API_PREFIX}' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/getfile?file_id={media_id}'
    result = requests.get(get_file_url)
    result_json = result.json()

    if result_json['ok'] is False \
            or result.status_code != 200 \
            or 'file is too big' in result_json.get('description', '').lower() \
            or 'bad request' in result_json.get('description', '').lower() \
            or not result_json.get('result', {}).get('file_path'):

        error_message = f'{result.status_code = }' \
                f'\n\n{result.text = }' \
                f'\n\n{result_json = }'
        error(error_message)
        send_message(chat_id=chat_id_to_send_error, message=error_message)
        return '', -1

    media_path = result_json['result']['file_path']
    media_size = result_json['result']['file_size']
    media_url = f'https://api.telegram.org/file/bot' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/{media_path}'
    return media_url, media_size


def get_bot_description(chat_id_to_send_error: int) -> str:
    get_description_url: str = f'{TELEGRAM_BOT_API_PREFIX}' \
            f'{cfg.TELEGRAM_BOT_TOKEN}/getMyDescription'
    result = requests.get(get_description_url)
    result_json = result.json()
    description: str = str(result_json.get('result', {}).get('description', ''))
    if result_json['ok'] is False \
            or result.status_code != 200 \
            or not description \
            or 'bad request' in description.lower():

        chat_id_to_send_error = cfg.TELEGRAM_BOT_CHAT_ID
        error_message = f'{result.status_code = }' \
                f'\n\n{result.text = }' \
                f'\n\n{result_json = }'
        info(error_message)
        send_message(chat_id=chat_id_to_send_error, message=error_message)
        return ''
    return description


def delete_webhook() -> None:
    warning('Deleting webhook ...')
    delete_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        '/deletewebhook'
    requests.get(delete_webhook_url)
    warning('Webhook deleted.')


def set_webhook() -> None:
    warning('Setting webhook ...')
    allowed_updates = ['message', 'edited_message']
    allowed_updates_jsons = json.dumps(allowed_updates)
    set_webhook_url = f'{TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
        f'/setwebhook?url={cfg.AWS_LAMBDA_API_GATEWAY_URL}' \
        f'&max_connections=2' \
        f'&allowed_updates={allowed_updates_jsons}' \

    requests.get(set_webhook_url)
    warning('Webhook is set.')
