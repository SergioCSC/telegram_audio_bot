import config as cfg

from google import genai
from google.genai import types
# from google.api_core.exceptions import InvalidArgument, ResourceExhausted
from google.genai.errors import ServerError, ClientError, \
        UnknownFunctionCallArgumentError, FunctionInvocationError
# import os

import tg
from logging import error, info, debug


def summarize(chat_id: int, text: str) -> str:

    APPROXIMATE_RUSSIAN_WORD_LENGTH = 5
    wanted_words_count = cfg.MIN_TEXT_LENGTH_TO_SUMMARIZE // APPROXIMATE_RUSSIAN_WORD_LENGTH
    short_length = wanted_words_count * 2 // 8
    long_length  = wanted_words_count * 5 // 8

    length_restriction_prompt = f"Please make 2 summaries: short and long." \
            f" Short summary should be exactly {short_length} words." \
            f" Long summary should be exactly {long_length} words." \
            f" Divide each summary into paragraphs, but don't mark them." \
            f" Don't use markdown."
            # f" Use asterics symbol before and after each summary header as a markdown symbol."

    prompt = f"You are a very professional document summarization specialist." \
            f" Please summarize the given document into the Russian language." \
            f" Please keep the style and do not add any additional information." \
            f" {length_restriction_prompt}: "
    
    model_response = _model_query(prompt, text, chat_id)
    return model_response


def recognize(chat_id: int, mime_type: str, file_ext: str, file_bytes: bytes) -> str:

    if mime_type.startswith('application/') \
            or mime_type.startswith('text/'):
        document_type = 'document'
    elif mime_type.startswith('image/') \
            or mime_type.startswith('video/'):
        document_type = 'image'
    else:
        return f'Unknown {mime_type = }'

    prompt = f"You are a very professional {document_type} recognition specialist." \
            f" Please give the full text from the given {document_type} into the Russian language." \
            f" Do not add any additional information."

    model_response = _model_query(prompt, file_bytes, chat_id, mime_type)
    return model_response


def _model_query(prompt: str, data: str | bytes, chat_id: int, mime_type=None) -> str:

    from youtube_conn import is_youtube_link
    
    def _subquery(prompt: str, data: str | bytes, model: str) -> types.GenerateContentResponse:
        
        if isinstance(data, str) and is_youtube_link(data):

            prompt = """
                    Analyze the following YouTube video content. Provide a concise summary in Russian covering:
                    1.  Main Thesis/Claim: What is the central point the creator is making?
                    2.  Key Topics: List the main subjects discussed, referencing specific examples or technologies mentioned (e.g., AI models, programming languages, projects).
                    3.  Call to Action: Identify any explicit requests made to the viewer.
                    4.  Summary: Provide a concise summary of the video content.
                    Use the provided title, chapter timestamps/descriptions, and description text for your analysis.
                    Don't use a markdown.
            """

            # prompt = "Generate a paragraph in Russian that summarizes this video. Keep it to 3 to 5 sentences with corresponding timecodes." 
            # prompt = "Transcribe the audio from this video into Russian" #  , giving timestamps for salient events in the audio. Provide timestamps without miliseconds!"
            # prompt = "Don't analyze the video. Just summarize the subtitles from it and return them in Russian." \
            # " If there are no subtitles, then summarize the text of the audio in Russian." \
            # @param ["Generate a paragraph that summarizes this video. Keep it to 3 to 5 sentences with corresponding timecodes.", 
            # "Choose 5 key shots from this video and put them in a table with the timecode, text description of 10 words or less, and a list of objects visible in the scene (with representative emojis).",
            # "Generate bullet points for the video. Place each bullet point into an object with the timecode of the bullet point in the video."
            tg.send_message(chat_id, "YouTube link detected. So using model: " + model)
            
            from youtube_conn import get_duration_from_youtube_link
            video_duration_sec = get_duration_from_youtube_link(data)

            fps = cfg.FRAMES_TO_ANALYZE * 1.0 / video_duration_sec
            
            config = types.GenerateContentConfig(
                media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
                system_instruction=prompt,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0) if not model.startswith('gemini-2.0') else None,  # Disables thinking
            )
            response = client.models.generate_content(
                model=model,
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=data),
                            video_metadata=types.VideoMetadata(fps=fps,)
                        ),
                        # types.Part(text=prompt)
                    ]
                ),
                config=config,
            )
            return response

        elif isinstance(data, bytes):
            tg.send_message(chat_id, "Try with Gemini model: " + model)
            config = types.GenerateContentConfig(
                system_instruction=prompt,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0) if not model.startswith('gemini-2.0') else None,  # Disables thinking
            )
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=data,
                        mime_type=mime_type,
                    ),
                ],
                config=config,
            )
            return response

        # Assuming data is a string of text
        config = types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_budget=0) if not model.startswith('gemini-2.0') else None,  # Disables thinking
        )
        response = client.models.generate_content(
                model=model,
                contents=[data],
                config = config,
        )
        return response
    
    client = genai.Client(api_key=cfg.GEMINI_API_KEY)
    model = cfg.GEMINI_YOUTUBE_MODEL_1ST_MODEL if is_youtube_link(data) else cfg.GEMINI_1ST_MODEL
    try:
        response = _subquery(prompt, data=data, model=model)
    except (ServerError, ClientError, \
            UnknownFunctionCallArgumentError, FunctionInvocationError) as e:
        error_str = f"Gemini exception: {e}" 
        if "unsupported" in str(e).lower():
            return error_str
        else:
            model = cfg.GEMINI_YOUTUBE_MODEL_2ND_MODEL if is_youtube_link(data) else cfg.GEMINI_2ND_MODEL
            tg.send_message(chat_id, f"{error_str}\n\nTrying again with {model = }")
            try:
                response = _subquery(prompt, data=data, model=model)
            except (ServerError, ClientError, \
                    UnknownFunctionCallArgumentError, FunctionInvocationError) as e:
                return f"Gemini exception: {e}"
        
    return response.text


if __name__ == "__main__":
    response = summarize("Write a story about a magic backpack.")
    print(response)