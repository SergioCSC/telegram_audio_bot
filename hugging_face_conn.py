import config as cfg
import tg
from utils import _init_logging

# from huggingface_hub import InferenceClient
from gradio_client import Client  #, handle_file
from gradio_client.utils import Status

from logging import error, warning, info, debug
import requests
import tempfile
import time


# import json


HUGGING_FACE_MODEL_URL_PREFIX = 'https://api-inference.huggingface.co/models/'


def _post(url: str, headers: dict, data: bytes) -> tuple[requests.Response, dict]:
    response = requests.post(url, headers=headers, data=data)
    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError as e:
        response_json = {'error': str(response.text)}
        error(f'Responce.text: {response.text} \
             \n\nError decoding JSON: {e}')
    return response, response_json


# def summarize(model: str, text: str) -> str:
#     debug('start')

#     client = InferenceClient(api_key=cfg.HUGGING_FACE_API_KEY)
#     completion = client.summarization(model=model, 
#                                       text=text,
#                                       parameters={'max_length': 75}
#                                       )
#     summary = completion.get('summary_text', '')

#     debug('finish')
#     return summary


def audio2text(model: str, audio: bytes) -> tuple[str, int]:
    debug('start')
    headers = {'Authorization': f'Bearer {cfg.HUGGING_FACE_API_KEY}'}
    url = HUGGING_FACE_MODEL_URL_PREFIX + model
    response, returned_json = _post(url, headers, audio)
    text = str(returned_json.get('text', ''))
    error = str(returned_json.get('error', ''))
    
    if response.status_code == 503 \
            and ('is currently loading' in error
                 or 'Service Unavailable' in error):
        sleeping_time = int(returned_json.get('estimated_time', 20)) + 1
        return error, sleeping_time

    elif response.status_code == 500 \
            and 'Internal Server Error' in error:
        return error, -1
    elif response.status_code == 413 \
            and 'payload reached size limit' in error:
        return error, -1

    # data = {'model': 'whisper-1', 'language': 'ru'}  # TODO get language from Telegram update language_code
    elif response.status_code == 200:
        if not text:
            text = 'Не смог найти слова в аудио, сорян'
        return text, -1
    else:
        text = f'Статус код ответа Hugging Face: {response.status_code}'
        if error:
            text = f'{text}\nСообщение об ошибке от Hugging Face: {error}'
    debug('finish')
    return text, -1


def downgrade(model_name: str) -> str:
    match model_name:
        # case 'openai/whisper-large-v3':
        case cfg.HUGGING_FACE_MODEL:
            return 'openai/whisper-medium'
        case 'openai/whisper-medium':
            return 'openai/whisper-small'
        case 'openai/whisper-small':
            return 'openai/whisper-base'
        case 'openai/whisper-base':
            return 'openai/whisper-tiny'
        case 'openai/whisper-tiny':
            return 'openai/whisper-tiny'
        case _:
            return model_name


def _audio2text_using_hf_model(model: str, audio_bytes: bytes, chat_id: int):
    output_text, sleeping_time = audio2text(model, audio_bytes)
    while 'is currently loading' in output_text:
        output_text = f'{output_text}   \
                        \n\nPlease wait {sleeping_time} seconds ...'
        warning(output_text)
        tg.send_message(chat_id, output_text)
        time.sleep(sleeping_time)
        tg.send_message(chat_id, 'Sending an audio to Hugging face ...')
        output_text, sleeping_time  \
                = audio2text(model, audio_bytes)
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

# output = query("sample1.flac")