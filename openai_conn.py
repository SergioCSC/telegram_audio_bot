import config as cfg

import requests

import io
import json

from logging import info, debug


OPENAI_TRANSCRIPTIONS_URL = 'https://api.openai.com/v1/audio/transcriptions'
OPENAI_CHAT_URL = 'https://api.openai.com/v1/chat/completions'


def audio2text(audio: io.BytesIO, voice_format: str) -> str:
    debug('start')
    headers = {'Authorization': f'Bearer {cfg.OPEN_AI_API_KEY}',
                        #    'Content-Type': 'multipart/form-data'
               }
    
    match voice_format:
        case 'wav': 
            file_format = 'audio/wav'
        case 'mp3': 
            file_format = 'audio/mpeg'
        case _:
            info(f'unknown audio format: {voice_format}')
            assert False

    files = [('file', (f'audio.{voice_format}', audio, file_format))]
    data = {'model': 'whisper-1', 'language': 'ru'}  # TODO get language from Telegram update language_code
    response = requests.post(url=OPENAI_TRANSCRIPTIONS_URL, 
            headers=headers,
            files=files,
            data=data,
            )
    d = response.json()
    if response.status_code == 200:
        text = d.get('text')
        if not text:
            text = 'Не смог найти слова в аудио, сорян'
    else:
        text = f'Статус код ответа OpenAI: {response.status_code}'
        if error_text := d.get('error', {}).get('message'):
            text = f'{text}\nСообщение об ошибке от OpenAI: {error_text}'
    debug('finish')
    return text
    
    # transcript = openai.Audio.transcribe("whisper-1", voice_wav, language='ru')
    # return transcript.text
    
    
def chat(input_text: str, temperature: float = 1) -> str:
    debug('start')

    headers = {'Authorization': f'Bearer {cfg.OPEN_AI_API_KEY}',
               'Content-Type': 'application/json'
              }
    data = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": input_text,
            }
        ],
        "temperature": temperature
    })

    response = requests.post(url=OPENAI_CHAT_URL, 
                  headers=headers,
                  data=data,
                  )
    d = response.json()
    if response.status_code == 200:
        text = d.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not text:
            text = 'Что-то не выходит нонче у Данилы каменный цветок ...'
    else:
        text = f'Статус код ответа OpenAI: {response.status_code}'
        if error_text := d.get('error', {}).get('message'):
            text = f'{text}\n\nСообщение об ошибке от OpenAI: {error_text}'

    debug('finish')
    return text