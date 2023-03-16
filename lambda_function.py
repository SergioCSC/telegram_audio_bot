import config as cfg
import api_keys
import tg
import transcoder
import transcriptor

import sys
import time
import requests
import logging
from logging import info, debug


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    debug('start')
    update_message = tg.get_update_message(event)
    chat_id, result_text = _get_chat_id_and_text(update_message)
    tg.send_message(chat_id, result_text)
    debug('finish')
    return {'statusCode': 200, 'body': 'Success'}


def _get_chat_id_and_text(message: dict) -> tuple[int, str]:
    debug('start')
    info(f'{message = }')
    if not message:
        return 0, ''

    chat_id = int(message.get('chat', {}).get('id', 0))
    if not chat_id:
        return 0, ''
    if message.get('voice'):
        voice_url = tg.get_voice_url(message)
        wav_in_memory = transcoder.transcode_opus_ogg_to_wav(voice_url)
        output_text = transcriptor.get_text(wav_in_memory)
    
    elif input_text := message.get('text'):
        output_text = transcriptor.chat(input_text)
    else:
        output_text = ''
    info(f'{output_text = }')
    debug('finish')
    return chat_id, output_text


def _init_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    datefmt='%H:%M:%S'
    FORMAT = "[%(asctime)s %(filename)20s:%(lineno)5s - %(funcName)25s() ] %(message)s"
    logging.basicConfig(level=logging.INFO,
                        format=FORMAT, 
                        datefmt=datefmt,
                        stream=sys.stdout)


def telegram_long_polling():
    _init_logging()
    info('start')
    tg.delete_webhook()

    timeout = 60
    offset = -2
    while True: 
        start_time = time.time()
        url = f'{tg.TELEGRAM_BOT_API_PREFIX}{api_keys.TELEGRAM_BOT_TOKEN}' \
                f'/getUpdates?offset={offset + 1}&timeout={timeout}'
        updates = requests.get(url).json()

        if updates['result']:
            for result in updates.get('result', []):
                offset = result.get('update_id', offset)
                message = result.get('message', {})
                chat_id, result_text = _get_chat_id_and_text(message)
                tg.send_message(chat_id, result_text)
        end_time = time.time()
        info(f'Время между запросами к Telegram Bot API: {end_time - start_time}')


if __name__ == '__main__':
    telegram_long_polling()