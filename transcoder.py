# This code uses opusdec library of opus audio codec 
# under three-clause BSD license.
# For details, see https://opus-codec.org/license/

# This code uses LAME mp3 encoder of The LAME Project
# under LGPL license.
# For details, see https://lame.sourceforge.io/


import config as cfg

import requests

import pathlib
import subprocess
from logging import info, debug


def transcode_wav_to_mp3(wav_bytes: bytes) -> bytes:
    info('start')
    
    if cfg.IN_LINUX:
        lame_path = str(pathlib.Path('lame'))  # apt install lame
    else:
        lame_path = str(pathlib.Path('lame', 'lame_win', 'lame.exe'))
    
    result = subprocess.run([lame_path,
                                '-f',
                                '-m',
                                'm',
                                '-',
                                '-',
                                ],
                            input=wav_bytes,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    
    mp3_bytes: bytes = result.stdout
    debug(f'{result.stderr = }')
    info('finish')
    return mp3_bytes


def transcode_opus_ogg_to_wav(source_url: str) -> bytes:
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
    
    debug(f'{result.stderr = }')
    info('finish')    
    return voice_wav_bytes
