import tempfile
import config as cfg

import google.generativeai as genai

import os

genai.configure(api_key=cfg.GEMINI_API_KEY)

def summarize(model_name: str, text: str | None = None, file_ext: str | None = None,
              file_bytes: bytes | None = None) -> str:

    model = genai.GenerativeModel(model_name=model_name)
    text = text if text else ''
    length_restriction_prompt = f"Please use about {cfg.TEXT_LENGTH_IN_WORDS_TO_SUMMARIZE} words or less"
    prompt = f"Summarize this into the Russian language. " \
            f"Please keep the style and do not add any additional information. " \
            f"{length_restriction_prompt}: {text}"
    
    if file_bytes:
        with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext,
                delete_on_close=False) as temp_file:
        
            temp_file.write(file_bytes)
            temp_file.close()
            uploaded_file: genai.types.file_types.File | None = genai.upload_file(temp_file.name)
                
        response = model.generate_content([prompt, uploaded_file])
    else:
        response = model.generate_content(prompt,
            # generation_config=genai.types.GenerationConfig(
            #         # max_output_tokens=50,
            #         # temperature=1.0,
            #         )
        )
    return response.text


if __name__ == "__main__":
    response = summarize("gemini-1.5-flash", "Write a story about a magic backpack.")
    print(response)