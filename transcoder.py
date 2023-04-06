import config as cfg

import requests

import io
import pathlib
import subprocess
from logging import info, debug


def transcode_opus_ogg_to_wav(source_url: str) -> io.BytesIO:
    info('start')
    if cfg.IN_LINUX:
        response = requests.get(source_url)
        ogg_bytes_io = response.content
        opus_path = str(pathlib.Path('opus', 'opus_linux', 'opusdec'))
        result = subprocess.run([opus_path, 
                                '--force-wav', 
                                '-',
                                '-'],
                                input=ogg_bytes_io,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )

    else:
        opus_path = str(pathlib.Path('opus', 'opus_win', 'opusdec.exe'))
        result = subprocess.run([opus_path, 
                                '--force-wav', 
                                source_url, 
                                '-'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )

    voice_wav_bytes: bytes = result.stdout
    voice_wav_bytes_io = io.BytesIO(voice_wav_bytes)
    voice_wav_bytes_io.name = 'my_voice_message.wav'
    
    debug(f'{result.stderr = }')
    info('finish')    
    return voice_wav_bytes_io
