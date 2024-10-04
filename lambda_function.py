import contextlib
import tempfile
import config as cfg
import tg
import transcoder
import openai_conn
import hugging_face_conn as hf

from gradio_client import Client  #, handle_file
from gradio_client.utils import Status
import requests

import io
import sys
import time
import logging
from logging import error, warning, info, debug


SUCCESSFULL_RESPONSE = {'statusCode': 200, 'body': 'Success'}
EMPTY_RESPONSE_STR = 'EMPTY_RESPONSE_STR'


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    warning('start')
    update_message: dict = tg.get_update_message(event)

    result_text, chat_id = _get_text_and_chat_id(update_message)

    if chat_id != -1:
        tg.send_message(chat_id, result_text)

    warning('finish')
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


def _audio2text_using_hf_model(model: str, audio_bytes: bytes, chat_id: int):
    output_text, sleeping_time = hf.audio2text(model, audio_bytes)
    while 'is currently loading' in output_text:
        output_text = f'{output_text}   \
                        \n\nPlease wait {sleeping_time} seconds ...'
        warning(output_text)
        tg.send_message(chat_id, output_text)
        time.sleep(sleeping_time)
        tg.send_message(chat_id, 'Sending an audio to Hugging face ...')
        output_text, sleeping_time  \
                = hf.audio2text(model, audio_bytes)
    return output_text

        
def _audio2text_using_hf_space(audio_bytes: bytes,
                               audio_ext: str,
                               chat_id: int,
                               tg_message_prefix: str) -> str:
    debug('start')
    try:

        with tempfile.NamedTemporaryFile(mode='wb',
                suffix=audio_ext,
                delete_on_close=False) as audio_file:

            audio_file.write(audio_bytes)
            audio_file.close()

            with open(audio_file.name, 'rb') as audio_file:
                client = Client(cfg.HUGGING_FACE_SPACE)
                _init_logging()
                # api_str = client.view_api(return_format='str')
                # debug(f'{api_str = }')
                
                # output_text = 
                job = client.submit(
                    # 'https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/audio_sample.wav',
                    # media_url,	# str (filepath or URL to file) in 'audio_path' Audio component
                    # param_0=handle_file(audio_file.name),
                    audio_file.name,
                    "transcribe",	# str in 'Task' Radio component
                    # True,	# bool in 'Group by speaker' Checkbox component
                    api_name="/predict"
                )
                while job.status().code == Status.STARTING:
                    time.sleep(5)
                while not job.status().code in (Status.FINISHED, Status.CANCELLED):
                    eta_seconds = int(job.status().eta - 1 if job.status().eta else 60)
                    waiting_message = f'{tg_message_prefix}\nSpace: {cfg.HUGGING_FACE_SPACE} \
                            \n\nEstimated time average: {eta_seconds} seconds \
                            \n\nSleep during this time ...'
                    if job.status().code == Status.IN_QUEUE:
                        queue_size = job.status().queue_size
                        waiting_message += f'\n\n{queue_size} in queue before us'
                    warning(waiting_message)
                    tg.send_message(chat_id, waiting_message)
                    time.sleep(eta_seconds)
                if job.status().success:
                    output_text = job.result() 
                else:
                    output_text = f'{tg_message_prefix}\n\n{job.status().code = }\n\n{job.exception() = }\n\nFailed'
                client.close()

    except ValueError as e:
        output_text = f'Failed. {type(e)} exception: {str(e)}' \
                    f'\nException args: {e.args}'

    debug('finish')
    return output_text


def _get_audio_bytes(media_url: str, message: dict) -> tuple[bytes, str]:
    response = requests.get(media_url)
    if message.get('video') or message.get('video_note') \
            or 'video' in message.get('document', {}).get('mime_type', ''):
        video_ext = message.get('video', message.get('document', {})) \
                .get('mime_type', '')
        video_ext = '.' + video_ext.split('/')[1] if video_ext else ''
        if not video_ext:
            if message.get('video_note'):
                video_ext = '.mp4'
            else:
                warning(f'unknown video type. {message = }')
        audio_bytes = transcoder.extract_mp3_from_video(response.content, video_ext)
        audio_ext = '.mp3'
    else:
        audio_bytes = response.content
        audio_ext = message.get('audio', message.get('voice', message.get('document', {}))) \
                .get('mime_type', '')
        audio_ext = '.' + audio_ext.split('/')[1] if audio_ext else ''
        if not audio_ext:
            warning(f'unknown audio type. {message = }')
            audio_ext = '.mp3'

    return audio_bytes, audio_ext


def _get_text_from_media(message: dict, chat_id: int) -> str:
    start_time = time.time()
    warning('start')
    debug(f'{message = }')
    
    model = cfg.HUGGING_FACE_MODEL
    prefix = _get_media_marker(message)

    tg.send_message(chat_id, f'{prefix} \
                    \n\nGetting media from Telegram ...')
    media_url, media_size = tg.get_media_url_and_size(message, chat_id)
    if not media_url:
        return ''
    
    if media_size > cfg.MAX_MEDIA_SIZE:
        output_text = f'{prefix}\n\nToo big media file ({_sizeof_fmt(media_size)}).'
    elif False: #_get_media_duration(message) > cfg.MEDIA_DURATION_TO_USE_SPACE:
       pass

    else:
        audio_bytes, audio_ext = _get_audio_bytes(media_url=media_url, message=message)
        audio_size = _sizeof_fmt(len(audio_bytes))
        tg.send_message(chat_id, f'{prefix}\nModel: {model} \
                        \n\nSending an audio ({audio_size}) to Hugging face ...'
                        )
        
        output_text = _audio2text_using_hf_model(model=model, audio_bytes=audio_bytes, chat_id=chat_id)
        # output_text = 'Internal Server Error'

        if 'Internal Server Error' in output_text \
                or 'Service Unavailable' in output_text \
                or 'the token seems invalid' in output_text \
                or 'payload reached size limit' in output_text \
                or 'Сообщение об ошибке от Hugging Face' in output_text:

            output_text = f'{prefix}\nModel: {model} \
                            \n\nText: Error: {output_text} \
                            \n\nTrying to use hugging face space ({cfg.HUGGING_FACE_SPACE}) ...'
            warning(output_text)
            tg.send_message(chat_id, output_text)
            
            output_text = _audio2text_using_hf_space(audio_bytes=audio_bytes,
                                                     audio_ext=audio_ext,
                                                     chat_id=chat_id,
                                                     tg_message_prefix=prefix)

            if not 'Internal Server Error' in output_text \
                    and not 'Service Unavailable' in output_text \
                    and not 'the token seems invalid' in output_text \
                    and not 'payload reached size limit' in output_text \
                    and not 'Сообщение об ошибке от Hugging Face' in output_text \
                    and not 'Failed' in output_text:

                output_text = f'{prefix}\nSpace: {cfg.HUGGING_FACE_SPACE} \
                                \n\nText: {output_text} \
                                \n\nCalc time: {int(time.time() - start_time)} seconds'
                return output_text
      
            while 'Internal Server Error' in output_text \
                    or 'Service Unavailable' in output_text \
                    or 'the token seems invalid' in output_text \
                    or 'payload reached size limit' in output_text \
                    or 'Сообщение об ошибке от Hugging Face' in output_text \
                    or 'Failed' in output_text:
                        
                if model == hf.downgrade(model):
                    message = f"Can't downgrade the smallest model.\n\nFinish"
                    warning(message)
                    tg.send_message(chat_id, message=message)
                    
                    output_text = f'{prefix}\nModel: {model} \
                            \n\nText: {output_text} \
                            \n\nCalc time: {int(time.time() - start_time)} seconds'
                    return output_text
                
                warning(output_text)
                tg.send_message(chat_id, 
                        f'{output_text}                                             \
                        \n\nDowngrade model to {hf.downgrade(model)} and repeat.    \
                        \nSending an audio to Hugging face ...'
                        )

                # output_text = f'{prefix}\nModel: {model}\n\nText: {output_text}'
                        
                model = hf.downgrade(model)
                output_text = _audio2text_using_hf_model(model=model, audio_bytes=audio_bytes, chat_id=chat_id)


    output_text = f'{prefix}\nModel: {model} \
            \n\nText: {output_text} \
            \n\nCalc time: {int(time.time() - start_time)} seconds'
    
    return output_text


def _get_text_and_chat_id(message: dict, chat_temp: float = 1) -> tuple[str, int]:
    
    if not message:
        error(f'EMPTY_RESPONSE_STR')
        return EMPTY_RESPONSE_STR, -1
    
    chat_id = int(message.get('chat', {}).get('id', 0))
    if not chat_id:
        error(f'EMPTY_RESPONSE_STR\n\n{chat_id = }\n\n{message = }')
        return EMPTY_RESPONSE_STR, -1

    if message.get('audio') or message.get('voice') \
            or message.get('video') or message.get('video_note') \
            or 'video' in message.get('document', {}).get('mime_type', '') \
            or 'audio' in message.get('document', {}).get('mime_type', ''):

        output_text = _get_text_from_media(message=message, chat_id=chat_id)

    elif input_text := message.get('text'):
        if not input_text or input_text.lower() == '/start':
            output_text = tg.get_bot_description(chat_id)
        else:
            tg.send_message(chat_id, 'I have to think about it. Just a moment ...')
            input_text = _correct_prompt(input_text)
            output_text = openai_conn.chat(input_text, chat_temp)

    else:
        error_message = f"Can't parse this type of Telegram message: {message}"
        error(error_message)
        output_text = "It seems I can't do what you want. \
                I can answer to text and transcribe audio into text."
        output_text += '\n\n' + error_message        

    debug(f'{output_text = }')
    warning('finish')
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
    logging.getLogger().setLevel(cfg.LOG_LEVEL)  # for local run
    warning('start')
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
        warning(f'time between requests to Telegram Bot API: {end_time - start_time}')


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