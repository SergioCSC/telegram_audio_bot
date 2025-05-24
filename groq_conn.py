import config as cfg
from data_structures import Model
from utils import _sizeof_fmt

import tempfile

import tg

def transcribe_audio(audio_bytes: bytes, 
                     audio_ext: str,
                     chat_id: int,
                     content_marker:str) -> tuple[str, str]:

    audio_size = _sizeof_fmt(len(audio_bytes))
    model = Model('Groq', cfg.GROQ_MODEL)

    tg.send_message(chat_id, f'{content_marker}\nmodel: {model} \
                    \n\nSending an audio ({audio_size}) to {model.site} ...'
                    )

    with tempfile.NamedTemporaryFile(mode='wb',
            suffix=audio_ext,
            delete_on_close=False) as audio_file:

        audio_file.write(audio_bytes)
        audio_file.close()

        with open(audio_file.name, 'rb') as audio_file:
            from groq import Groq, GroqError
            groq_client = Groq()
            try:
                transcription = groq_client.audio.transcriptions.create(
                    file=(audio_file.name, audio_file.read()),
                    model="whisper-large-v3",
                    # prompt="Specify context or spelling",  # Optional
                    # response_format="json",  # Optional
                    # language="en",  # Optional
                    # temperature=0.0  # Optional
                )
            except GroqError as e:
                output_text = f'model {model} failed. Exception: {str(e)}'
                output_text = f'{content_marker}\n\nText: {output_text}'
                
                tg.send_message(chat_id, output_text)
                return '', model.name
            return transcription.text, model.name
    