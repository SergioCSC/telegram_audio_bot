from logging import warning
import time
import tg
from utils import _sizeof_fmt
from data_structures import Model
import config as cfg


from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
    DeepgramError,
)

import httpx

def transcribe_audio(audio_bytes: bytes, 
                     audio_ext: str,
                     chat_id: int,
                     content_marker: str) -> tuple[str, str]:

    start_time = time.time()

    audio_size = _sizeof_fmt(len(audio_bytes))
    model = Model('Deepgram', cfg.DEEPGRAM_MODEL)
    tg.send_message(chat_id, f'{content_marker}\nmodel: {model} \
            \n\nSending an audio ({audio_size}) to {model.site} ...'
    )

    deepgram = DeepgramClient(cfg.DEEPGRAM_API_KEY)
    payload: FileSource = {
        "buffer": audio_bytes,
    }
    options = PrerecordedOptions(
        # model="nova-2",
        model=model.name,
        detect_language=True,
        smart_format=True,
        # diarize=True,
        # summarize=True,
        # topics=True,
        # paragraphs=True,
        # punctuate=True,
        # utterances=True,
        # utt_split=0.8,
        # detect_entities=True,
        # intents=True,
    )
    myTimeout = httpx.Timeout(None, connect=20.0)
    try:
        # raise Exception('Deepgram is not available')
        response = deepgram.listen.rest.v("1").transcribe_file(
                payload, options, timeout=myTimeout)
        alternatives = response["results"]["channels"][0]["alternatives"]
        if alternatives:
            output_text = alternatives[0]["transcript"]
        else:
            raise DeepgramError("empty answer from Deepgram")
    except Exception as e:

        output_text = f'model {model} failed. Exception: {str(e)}'
        output_text = f'{content_marker}\n\nText: {output_text}'
        
        model = Model('Hugging_face', cfg.HUGGING_FACE_MODEL)

        tg.send_message(chat_id, 
                        f'{output_text}                                             \
                        \n\nSending an audio to model {model} and repeat ...'
                        )
        # Try to use Hugging Face model
        from hugging_face_conn import _audio2text_using_hf_model
        output_text = _audio2text_using_hf_model(model=model.name, audio_bytes=audio_bytes, chat_id=chat_id)
        # output_text = 'Internal Server Error'

        if 'Internal Server Error' in output_text \
                or 'Service Unavailable' in output_text \
                or 'the token seems invalid' in output_text \
                or 'payload reached size limit' in output_text \
                or 'Сообщение об ошибке от Hugging Face' in output_text:

            output_text = f'{content_marker}\nmodel: {model} \
                            \n\nText: Error: {output_text} \
                            \n\nTrying to use hugging face space ({cfg.HUGGING_FACE_SPACE}) ...'
            warning(output_text)
            tg.send_message(chat_id, output_text)
            
            # Try to use Hugging Face space
            from hugging_face_conn import _audio2text_using_hf_space
            output_text = _audio2text_using_hf_space(audio_bytes=audio_bytes,
                                                        audio_ext=audio_ext,
                                                        chat_id=chat_id,
                                                        tg_message_prefix=content_marker)

            if not 'Internal Server Error' in output_text \
                    and not 'Service Unavailable' in output_text \
                    and not 'the token seems invalid' in output_text \
                    and not 'payload reached size limit' in output_text \
                    and not 'Сообщение об ошибке от Hugging Face' in output_text \
                    and not 'Failed' in output_text:

                output_text = f'{content_marker}\nSpace: {cfg.HUGGING_FACE_SPACE} \
                                \n\nText: {output_text} \
                                \n\nCalc time: {int(time.time() - start_time)} seconds'
                return output_text
    
            while 'Internal Server Error' in output_text \
                    or 'Service Unavailable' in output_text \
                    or 'the token seems invalid' in output_text \
                    or 'payload reached size limit' in output_text \
                    or 'Сообщение об ошибке от Hugging Face' in output_text \
                    or 'Failed' in output_text:
                        
                from hugging_face_conn import downgrade as hf_downgrade
                if model.name == hf_downgrade(model.name):
                    message = f"Can't downgrade the smallest model.\n\nFinish"
                    warning(message)
                    tg.send_message(chat_id, message=message)
                    
                    output_text = f'{content_marker}\nHugging face model: {model} \
                            \n\nText: {output_text} \
                            \n\nCalc time: {int(time.time() - start_time)} seconds'
                    return output_text
                
                warning(output_text)
                tg.send_message(chat_id, 
                        f'{output_text}                                             \
                        \n\nDowngrade Hugging face model to {hf_downgrade(model)} and repeat.    \
                        \nSending an audio to Hugging face ...'
                        )

                model = Model(model.site, hf_downgrade(model.name))
                output_text = _audio2text_using_hf_model(model=model, audio_bytes=audio_bytes, chat_id=chat_id)

    return output_text, model.name
