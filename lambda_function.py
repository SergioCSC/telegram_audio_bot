import tg
import transcoder
import transcriptor

import sys
import logging
from logging import info, debug


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    debug('start')
    chat_id, result_text = _get_chat_id_and_text(event)
    tg.send_message(chat_id, result_text)
    debug('finish')
    return {'statusCode': 200, 'body': 'Success'}


def _get_chat_id_and_text(event: dict) -> tuple[int, str]:
    update_message = tg.get_update_message(event)
    info(f'{update_message = }')
    if not update_message or not update_message.get('voice'):
        return 0, ''

    chat_id = int(update_message.get('chat', {}).get('id', 0))
    result_text = _get_text(update_message) if chat_id else ''
    return chat_id, result_text


def _get_text(message: dict) -> str:
    debug('start')
    voice_url = tg.get_voice_url(message)
    wav_in_memory = transcoder.transcode_opus_ogg_to_wav(voice_url)
    message_text = transcriptor.get_text(wav_in_memory)
    info(f'{message_text = }')
    debug('finish')
    return message_text


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