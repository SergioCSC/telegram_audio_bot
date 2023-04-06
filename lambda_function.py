import config as cfg
import tg
import transcoder
import openai_conn

import requests

import io
import sys
import time
import logging
from logging import info, debug


SUCCESSFULL_RESPONSE = {'statusCode': 200, 'body': 'Success'}


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    debug('start')
    update_message = tg.get_update_message(event)
    
    info(f'{update_message = }')
    if not update_message:
        return SUCCESSFULL_RESPONSE
    
    chat_id = int(update_message.get('chat', {}).get('id', 0))
    if not chat_id:
        return SUCCESSFULL_RESPONSE
    
    if 'voice' in update_message or 'audio' in update_message:
        tg.send_message(chat_id, 'Слушаю сообщение, думаю ...')
        result_text = _get_text(update_message)
    elif 'text' in update_message:
        tg.send_message(chat_id, 'Тут надо подумать, прежде чем ответить. Сейчас ...')
        result_text = _get_text(update_message)
    else:
        result_text = 'Кажется, я не умею того, чего вы хотите.' \
            ' Я умею отвечать на текст и расшифровывать аудио'
    
    tg.send_message(chat_id, result_text)
    debug('finish')
    return SUCCESSFULL_RESPONSE


def startswith(s: str, templates: list[str]) -> str:
    s = s.lower()
    for t in templates:
        if s.startswith(t):
            return t
    return ''


def correct_by_phrases(prompt: str, key_phrases: tuple[str], new_phrase: str) -> str:
    if key_phrase := startswith(prompt, key_phrases):
        prompt = new_phrase + '\n\n' + prompt[len(key_phrase):]
        return prompt
    return ''


def correct_prompt(prompt: str) -> str:
    key_phrases = ('correct:', 'corect:', 'исправь:', 'поправь:', 'правь:')
    if corrected_prompt := correct_by_phrases(prompt, 
            key_phrases, 
            'Correct this text:'
            ):
        return corrected_prompt
    
    key_phrases = ('translate:', 'translation:', 'переведи:', 'перевод:')
    if corrected_prompt := correct_by_phrases(prompt, 
            key_phrases, 
            'Translate text from standard English to Russian or vice versa:'
            ):
        return corrected_prompt
    
    return prompt
    

def _get_text(message: dict, chat_temp: float = 1) -> str:
    debug('start')

    if message.get('audio'):
        audio_url = tg.get_audio_url(message)
        response = requests.get(audio_url)
        mp3_bytes_io = io.BytesIO(response.content)
        output_text = openai_conn.audio2text(mp3_bytes_io, 'mp3')
        
    elif message.get('voice'):
        voice_url = tg.get_audio_url(message)
        wav_bytes_io = transcoder.transcode_opus_ogg_to_wav(voice_url)
        output_text = openai_conn.audio2text(wav_bytes_io, 'wav')

    elif input_text := message.get('text'):
        input_text = correct_prompt(input_text)
        output_text = openai_conn.chat(input_text, chat_temp)

    else:
        info(f"can't parse this type of message: {message}")
        assert False  # TODO really?

    info(f'{output_text = }')
    debug('finish')
    return output_text


def _init_logging() -> None:
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


def telegram_long_polling():
    _init_logging()
    info('start')
    tg.delete_webhook()

    timeout = 60
    offset = -2
    while True: 
        start_time = time.time()
        url = f'{tg.TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
                f'/getUpdates?offset={offset + 1}&timeout={timeout}'
        updates = requests.get(url).json()

        if updates['result']:
            for result in updates.get('result', []):
                offset = result.get('update_id', offset)
                message = result.get('message', {})
                chat_id = int(message.get('chat', {}).get('id', 0))
                if chat_id:
                    result_text = _get_text(message)
                    tg.send_message(chat_id, result_text)
        end_time = time.time()
        info(f'Время между запросами к Telegram Bot API: {end_time - start_time}')


if __name__ == '__main__':
    # tg.delete_webhook()
    # time.sleep(1)
    tg.set_webhook()
    # telegram_long_polling()
    pass