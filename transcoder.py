# This code uses opusdec library of opus audio codec 
# under three-clause BSD license.
# For details, see https://opus-codec.org/license/

# This code uses LAME mp3 encoder of The LAME Project
# under LGPL license.
# For details, see https://lame.sourceforge.io/


import config as cfg

import requests
import audio_extract

import tempfile
import pathlib
import subprocess
from logging import info, debug


def transcode_wav_to_mp3(wav_bytes: bytes) -> bytes:
    debug('start')
    
    if cfg.IN_LINUX:
        lame_path = str(pathlib.Path('lame'))  # apt install lame
    else:
        lame_path = str(pathlib.Path('lame', 'lame_win', 'lame.exe'))
    
    result = subprocess.run([lame_path,
                                '-s',
                                '16',
                                '--resample',
                                '16',
                                '-f',
                                '--abr',
                                '56',
                                '-m',
                                'm',
                                '-',
                                '-',
                                ],
                            input=wav_bytes,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    
    mp3_bytes: bytes = result.stdout
    # debug(f'{result.stderr = }')
    debug(f'finish')
    return mp3_bytes


def transcode_opus_ogg_to_wav(source_url: str) -> bytes:
    debug('start')
    if cfg.IN_LINUX:
        response = requests.get(source_url)
        ogg_bytes = response.content
        opus_path = str(pathlib.Path('opus', 'opus_linux', 'opusdec'))
        result = subprocess.run([opus_path, 
                                '--force-wav',
                                '--rate',
                                '16000',
                                '-',
                                '-'],
                                input=ogg_bytes,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )

    else:
        opus_path = str(pathlib.Path('opus', 'opus_win', 'opusdec.exe'))
        result = subprocess.run([opus_path, 
                                '--force-wav',
                                '--rate',
                                '16000',
                                source_url, 
                                '-'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )

    voice_wav_bytes: bytes = result.stdout
    
    debug(f'{result.stderr = }')
    debug(f'finish')
    return voice_wav_bytes


def extract_mp3_from_video(mp4_bytes: bytes, video_ext: str) -> bytes:
    debug('start')
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix=video_ext, 
            delete_on_close=False) as video_file:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3',
                ) as audio_file:
            video_filename = video_file.name
            audio_filename = audio_file.name

            video_file.write(mp4_bytes)
            video_file.close()
            audio_file.close()  # TODO why we have to close and open audio file?

            with open(video_filename, 'rb') as video_file:
                with open(audio_filename, 'wb') as audio_file:
                    audio_extract.extract_audio(input_path=video_filename,
                                                output_path=audio_filename,
                                                output_format='mp3', 
                                                overwrite=True)

            with open(audio_filename, 'rb') as audio_file:
                mp3_bytes = audio_file.read()

    audio_file = pathlib.Path(audio_filename)
    if audio_file.exists():
        audio_file.unlink()
            
    debug('finish')
    return mp3_bytes
