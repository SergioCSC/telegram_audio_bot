import contextlib
import config as cfg
import tg
import transcoder
import openai_conn
import hugging_face_conn as hf

from gradio_client import Client, file
import requests

import io
import sys
import time
import logging
from logging import info, debug


SUCCESSFULL_RESPONSE = {'statusCode': 200, 'body': 'Success'}
EMPTY_RESPONSE_STR = 'EMPTY_RESPONSE_STR'


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    debug('start')
    update_message: dict = tg.get_update_message(event)

    result_text, chat_id = _get_text_and_chat_id(update_message)

    if chat_id != -1:
        tg.send_message(chat_id, result_text)

    debug('finish')
    return SUCCESSFULL_RESPONSE


def _startswith(s: str, templates: list[str]) -> str:
    s = s.lower()
    for t in templates:
        if s.startswith(t):
            return t
    return ''


def _correct_by_phrases(prompt: str, key_phrases: list[str], new_phrase: str) -> str:
    if key_phrase := _startswith(prompt, key_phrases):
        prompt = new_phrase + '\n\n' + prompt[len(key_phrase):]
        return prompt
    return ''


def _correct_prompt(prompt: str) -> str:
    key_phrases = ['correct:', 'corect:', 'исправь:', 'поправь:', 'правь:']
    if corrected_prompt := _correct_by_phrases(prompt, 
            key_phrases, 
            'Correct this text:'
            ):
        return corrected_prompt
    
    key_phrases = ['translate:', 'translation:', 'переведи:', 'перевод:']
    if corrected_prompt := _correct_by_phrases(prompt, 
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


def _get_media_duration(message: dict) -> int:
    duration = message.get('audio', message.get('voice', \
            message.get('video', message.get('video_note', {})))) \
            .get('duration', -1)
    return duration


def _get_media_marker(message: dict) -> str:
    if caption := message.get('caption'):
        words = 5
        caption = ' '.join(str(caption).split(maxsplit=words)[:words])
        return f'Media caption: {caption}'
    if filename := message.get('audio', message.get('document',{})) \
        .get('file_name', ''):
        return f'Media file name: {filename}'
    duration = _get_media_duration(message)
    return f'Media duration: {duration} seconds'


@contextlib.contextmanager
def silence():
    sys.stderr, old = io.StringIO(), sys.stderr
    try:
        yield
    finally:
        sys.stderr = old


def _get_text_and_chat_id(message: dict, chat_temp: float = 1) -> tuple[str, int]:
    start_time = time.time()
    debug('start')
    debug(f'{message = }')
    
    if not message:
        debug(f'EMPTY_RESPONSE_STR')
        return EMPTY_RESPONSE_STR, -1
    
    chat_id = int(message.get('chat', {}).get('id', 0))
    if not chat_id:
        debug(f'EMPTY_RESPONSE_STR\n\n{chat_id = }\n\n{message = }')
        return EMPTY_RESPONSE_STR, -1

    if message.get('audio') or message.get('voice') \
            or message.get('video') or message.get('video_note') \
            or 'video' in message.get('document', {}).get('mime_type', '') \
            or 'audio' in message.get('document', {}).get('mime_type', ''):

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

        model = cfg.HUGGING_FACE_MODEL
        prefix = _get_media_marker(message)

        tg.send_message(chat_id, f'{prefix} \
                        \n\nGetting media from Telegram ...')
        media_url, media_size = tg.get_media_url_and_size(message, chat_id)
        if not media_url:
            return '', chat_id
        
        if media_size > cfg.MAX_MEDIA_SIZE:
            output_text = f'{prefix}\n\nToo big media file ({_sizeof_fmt(media_size)}).'
        elif True: #_get_media_duration(message) > cfg.MEDIA_DURATION_TO_USE_SPACE:
            with silence():
                client = Client(cfg.HUGGING_FACE_SPACE, verbose=False)

                # api_str = client.view_api()
                # debug(f'{api_str = }')

                # # create a text trap and redirect stdout
                # text_trap = io.StringIO()
                # sys.stdout = text_trap
                # sys.stderr = text_trap

                try:
                    output_text = client.predict(
                            # "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/audio_sample.wav",	# str (filepath or URL to file) in 'inputs' Audio component
                            media_url,
                            # inputs=file(media_url),
                            "transcribe",	# str in 'Task' Radio component
                            api_name="/predict",
                    )
                except ValueError as e:
                    output_text = f'{type(e)} exception: {str(e)}' \
                                f'\nException args: {e.args}'
                finally:
                    # now restore stdout function
                    pass
                    # sys.stdout = sys.__stdout__
                    # sys.stderr = sys.__stderr__


        else:
        
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

        output_text = f'{prefix}\nModel: {model} \
                \n\nText: {output_text} \
                \n\nCalc time: {int(time.time() - start_time)} seconds'

    elif input_text := message.get('text'):
        if not input_text or input_text.lower() == '/start':
            output_text = tg.get_bot_description(chat_id)
        else:
            tg.send_message(chat_id, 'I have to think about it. Just a moment ...')
            input_text = _correct_prompt(input_text)
            output_text = openai_conn.chat(input_text, chat_temp)

    else:
        error_message = f"Can't parse this type of Telegram message: {message}"
        info(error_message)
        output_text = "It seems I can't do what you want. \
                I can answer to text and transcribe audio into text."
        output_text += '\n\n' + error_message        

    debug(f'{output_text = }')
    debug('finish')
    return output_text, chat_id


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
                result_text, chat_id = _get_text_and_chat_id(message)
                if chat_id != -1:
                    tg.send_message(chat_id, result_text)
        end_time = time.time()
        debug(f'time between requests to Telegram Bot API: {end_time - start_time}')


if __name__ == '__main__':
    tg.set_webhook()

    # sys.stdout = sys.__stdout__
    # sys.stderr = sys.__stderr__
    
    # try:
    #     telegram_long_polling()
    # except KeyboardInterrupt as e:
    #     tg.set_webhook()
    #     raise e
    # pass