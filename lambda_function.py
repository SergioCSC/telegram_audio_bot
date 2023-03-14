import tg
import transcoder
import transcriptor

import sys
import logging
from logging import info, debug


def lambda_handler(event: dict, context) -> dict:
    init_logging()
    info('start')
    update_message = tg.get_update_message(event)
    info(f'{update_message = }')
    if update_message and update_message.get('voice'):
        chat_id = int(update_message['chat']['id'])
        result_text = get_text(update_message)
        tg.send_message(chat_id, result_text)
    info('finish')
    return {'statusCode': 200, 'body': 'Success'}


def get_text(message: dict) -> str:
    info('start')
    voice_url = tg.get_voice_url(message)
    wav_in_memory = transcoder.transcode_opus_ogg_to_wav(voice_url)
    message_text = transcriptor.get_text(wav_in_memory)
    info(f'{message_text = }')
    info('finish')
    return message_text


def init_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    datefmt='%H:%M:%S'
    FORMAT = "[%(asctime)s %(filename)20s:%(lineno)5s - %(funcName)25s() ] %(message)s"
    logging.basicConfig(level=logging.DEBUG,
                        format=FORMAT, 
                        datefmt=datefmt,
                        stream=sys.stdout)
