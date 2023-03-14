import api_keys

import io
import requests

from logging import info


OPENAI_TRANSCRIPTIONS_URL = 'https://api.openai.com/v1/audio/transcriptions'


def get_text(voice_wav: io.BytesIO) -> str:
    info('start')
    headers = {'Authorization': f'Bearer {api_keys.OPEN_AI_API_KEY}',
                        #    'Content-Type': 'multipart/form-data'
               }
    files = [('file', ('audio.wav', voice_wav, 'audio/wav'))]
    data = {'model': 'whisper-1', 'language': 'ru'}
    response = requests.post(url=OPENAI_TRANSCRIPTIONS_URL, 
                  headers=headers,
                  files=files,
                  data=data,
                  )
    d = response.json()
    if response.status_code == 200:
        text = d.get('text')
        if not text:
            text = 'Не смог найти слова в голосовухе, сорян'
    else:
        text = f'Статус код ответа OpenAI: {response.status_code}'
        if error_text := d.get('error', {}).get('message'):
            text = f'{text}\nСообщение об ошибке от OpenAI: {error_text}'
    info('finish')
    return text
    
    # transcript = openai.Audio.transcribe("whisper-1", voice_wav, language='ru')
    # return transcript.text