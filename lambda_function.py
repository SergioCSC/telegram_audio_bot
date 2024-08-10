import config as cfg
import tg
import transcoder
import openai_conn
import hugging_face_conn as hf

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
    update_message: dict = tg.get_update_message(event)
    
    debug(f'{update_message = }')
    if not update_message:
        return SUCCESSFULL_RESPONSE
    
    chat_id = int(update_message.get('chat', {}).get('id', 0))
    if not chat_id:
        return SUCCESSFULL_RESPONSE
    
    if 'voice' in update_message \
            or 'audio' in update_message \
            or 'video' in update_message \
            or 'video_note' in update_message \
            or 'video' in update_message.get('document', {}).get('mime_type', ''):
        
        result_text = _get_text(update_message)
    
    elif 'text' in update_message:
        input_text = update_message.get('text')
        
        if not input_text or input_text.lower() == '/start':
            result_text = '''

With me you can:

  - Ask something from chatGPT: Just text me
  - Transcribe an audio or a voice message: Send it to me
  - Fix grammar in text in any language. Write "correct: my_text" or "правь: мой_текст"
  - Translate text into English or Russian. Write: "translate: my_text"  or "переведи: мой текст"

The bot doesn't collect any info. Author: @n_log_n

                    '''
        else:
            tg.send_message(chat_id, 'I have to think about it. Just a moment ...')
            result_text = _get_text(update_message)
    else:
        result_text = "It seems I can't do what you want. \
                I can answer to text and transcribe audio into text."
    
    tg.send_message(chat_id, result_text)
    debug('finish')
    return SUCCESSFULL_RESPONSE


def startswith(s: str, templates: list[str]) -> str:
    s = s.lower()
    for t in templates:
        if s.startswith(t):
            return t
    return ''


def correct_by_phrases(prompt: str, key_phrases: list[str], new_phrase: str) -> str:
    if key_phrase := startswith(prompt, key_phrases):
        prompt = new_phrase + '\n\n' + prompt[len(key_phrase):]
        return prompt
    return ''


def _correct_prompt(prompt: str) -> str:
    key_phrases = ['correct:', 'corect:', 'исправь:', 'поправь:', 'правь:']
    if corrected_prompt := correct_by_phrases(prompt, 
            key_phrases, 
            'Correct this text:'
            ):
        return corrected_prompt
    
    key_phrases = ['translate:', 'translation:', 'переведи:', 'перевод:']
    if corrected_prompt := correct_by_phrases(prompt, 
            key_phrases, 
            'Translate text from standard English to Russian or vice versa:'
            ):
        return corrected_prompt
    
    return prompt


def _sizeof_fmt(num:int, suffix: str = "B") -> str:
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            rounded_down_num = num // 0.1 / 10
            return f"{rounded_down_num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"
    

def _get_text(message: dict, chat_temp: float = 1) -> str:
    debug('start')
    
    model = cfg.HUGGING_FACE_MODEL
    chat_id = message.get('chat', {}).get('id', 0)
    
    if message.get('audio') or message.get('voice') \
            or message.get('video') or message.get('video_note') \
            or 'video' in message.get('document', {}).get('mime_type', ''):
        
        filename = message.get('audio', message.get('document',{})) \
                .get('file_name', '')
        if filename:
            prefix = f'Media: {filename}'
        else:
            duration = message.get('audio', message.get('voice', \
                    message.get('video', message.get('video_note',{})))) \
                    .get('duration', -1)
            prefix = f'Duration: {duration} seconds'

        if message.get('voice'):
            # send_text = 'Decoding OGG --> WAV ...'
            # debug(send_text)
            # tg.send_message(chat_id, send_text)
            # wav_bytes = transcoder.transcode_opus_ogg_to_wav(voice_url)
            # send_text = f'WAV size: {len(wav_bytes)}\n\nEncoding WAV --> MP3 ...'
            # debug(send_text)
            # tg.send_message(chat_id, send_text)
            # mp3_bytes = transcoder.transcode_wav_to_mp3(wav_bytes)
            # send_text = f'MP3 size: {len(mp3_bytes)}'
            # debug(send_text)
            # tg.send_message(chat_id, send_text)
            # mp3_bytes_io: io.BytesIO = io.BytesIO(mp3_bytes)
            # mp3_bytes_io.name = 'my_audio_message.mp3'
            # output_text = openai_conn.audio2text(mp3_bytes_io, 'mp3')
            pass
        tg.send_message(chat_id, f'{prefix}\nModel: {model} \
                        \n\nGetting media from Telegram ...')
        media_url = tg.get_media_url(message, chat_id)
        if not media_url:
            return ''
        response = requests.get(media_url)
        if message.get('video') or message.get('video_note') \
                or 'video' in message.get('document', {}).get('mime_type', ''):
            video_ext = message.get('video', message.get('document', {})) \
                    .get('mime_type', '')
            if not video_ext:
                if message.get('video_note'):
                    video_ext = 'video/mp4'
                else:
                    debug(f'unknown {message = }')
            video_ext = '.' + video_ext.split('/')[1]
            audio_bytes = transcoder.extract_mp3_from_video(response.content, video_ext)
        else:
            audio_bytes = response.content
        audio_size = _sizeof_fmt(len(audio_bytes))
        tg.send_message(chat_id, f'{prefix}\nModel: {model} \
                        \n\nSending audio ({audio_size}) to Hugging face ...'
                       )
        output_text, sleeping_time = hf.audio2text(model, audio_bytes)

        while 'Internal Server Error' in output_text \
                or 'Service Unavailable' in output_text \
                or 'is currently loading' in output_text:
            
            
            output_text = f'{prefix}\nModel: {model}\n\nText: {output_text}'
            if 'Internal Server Error' in output_text \
                    or 'Service Unavailable' in output_text:
                if model == hf.downgrade(model):
                    tg.send_message(chat_id, 
                             f"Can't downgrade the smallest model.\n\nFinish"
                            )
                    break
                debug(output_text)
                tg.send_message(chat_id, 
                        f'{output_text}                                             \
                        \n\nDowngrade model to {hf.downgrade(model)} and repeat.    \
                        \nSending audio to Hugging face ...'
                        )
                model = hf.downgrade(model)
                output_text, sleeping_time  \
                        = hf.audio2text(model, audio_bytes)
            
            elif 'is currently loading' in output_text:
                output_text = f'{output_text}   \
                        \n\nPlease wait {sleeping_time} seconds ...'
                debug(output_text)
                tg.send_message(chat_id, output_text)
                time.sleep(sleeping_time)
                tg.send_message(chat_id, 'Sending audio to Hugging face ...')
                output_text, sleeping_time  \
                        = hf.audio2text(model, audio_bytes)
        
        output_text = f'{prefix}\nModel: {model}\n\nText: {output_text}'

    elif input_text := message.get('text'):
        input_text = _correct_prompt(input_text)
        output_text = openai_conn.chat(input_text, chat_temp)

    else:
        info(f"can't parse this type of message: {message}")
        assert False  # TODO really?

    debug(f'{output_text = }')
    debug('finish')
    return output_text


def _init_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    datefmt='%H:%M:%S'
    FORMAT = "[%(asctime)s %(filename)20s:%(lineno)5s - %(funcName)25s() ] %(message)s"
    logging.basicConfig(level=cfg.LOG_LEVEL,
                        format=FORMAT, 
                        datefmt=datefmt,
                        stream=sys.stdout)


def telegram_long_polling():
    _init_logging()
    logging.getLogger().setLevel(logging.DEBUG)  # for local run
    debug('start')
    tg.delete_webhook()
    time.sleep(1)
    
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
        debug(f'time between requests to Telegram Bot API: {end_time - start_time}')


if __name__ == '__main__':
    # tg.set_webhook()
    telegram_long_polling()
    pass