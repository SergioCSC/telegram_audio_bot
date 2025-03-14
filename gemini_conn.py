import tempfile
import config as cfg

import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted

import os

import tg


genai.configure(api_key=cfg.GEMINI_API_KEY)


def summarize(chat_id: int, text: str) -> str:

    short_length = cfg.TEXT_LENGTH_TO_SUMMARIZE // 4
    long_length = cfg.TEXT_LENGTH_TO_SUMMARIZE * 3 // 4
    length_restriction_prompt = f"Please make 2 summaries: short and long." \
            f" Short summary should be exactly {short_length} characters." \
            f" Long summary should be exactly {long_length} characters." \
            f" Divide each summary into paragraphs, but don't mark them."
            # f" Use asterics symbol before and after each summary header as a markdown symbol."

    prompt = f"You are a very professional document summarization specialist." \
            f" Please summarize the given document into the Russian language." \
            f" Please keep the style and do not add any additional information." \
            f" {length_restriction_prompt}: {text}"
    
    try:
        model_name = cfg.GEMINI_PRO_MODEL
        tg.send_message(chat_id, "Try with Gemini model: " + model_name)
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt,
            # generation_config=genai.types.GenerationConfig(
            #         # max_output_tokens=50,
            #         # temperature=1.0,
            #         )
        )
    except ResourceExhausted as e:
        model_name = cfg.GEMINI_FLASH_MODEL
        tg.send_message(chat_id, "Try with Gemini model: " + model_name)
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt,
            # generation_config=genai.types.GenerationConfig(
            #         # max_output_tokens=50,
            #         # temperature=1.0,
            #         )
        )
    return response.text


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

    with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext,
            delete_on_close=False) as temp_file:
    
        temp_file.write(file_bytes)
        temp_file.close()
    
        try:
            model_name = cfg.GEMINI_PRO_MODEL
            
            print("List of models that support generateContent:\n")
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    print(f'generateContent: {m.name}')

            print("List of models that support embedContent:\n")
            for m in genai.list_models():
                if "embedContent" in m.supported_generation_methods:
                    print(f'embedContent: {m.name}')
            
            tg.send_message(chat_id, "Try with Gemini model: " + model_name)
            model = genai.GenerativeModel(model_name=model_name)
            uploaded_file = genai.upload_file(temp_file.name)
            model_response = model.generate_content([prompt, uploaded_file])
        except ResourceExhausted as e:
            try:
                model_name = cfg.GEMINI_FLASH_MODEL
                tg.send_message(chat_id, "Try with Gemini model: " + model_name)
                model = genai.GenerativeModel(model_name=model_name)
                uploaded_file = genai.upload_file(temp_file.name)
                model_response = model.generate_content([prompt, uploaded_file])
            except (InvalidArgument, ValueError, FileNotFoundError) as e:
                return f'{model_name} failed\n{mime_type = }\n{file_ext = }\nException: {str(e)}'
        except (InvalidArgument, ValueError, FileNotFoundError) as e:
            return f'{model_name} failed\n{mime_type = }\n{file_ext = }\nException: {str(e)}'

    return model_response.text


if __name__ == "__main__":
    response = summarize("Write a story about a magic backpack.")
    print(response)