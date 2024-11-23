import config as cfg

import google.generativeai as genai

import os

genai.configure(api_key=cfg.GEMINI_API_KEY)

def summarize(model_name: str, text: str) -> str:
    model = genai.GenerativeModel(model_name=model_name)
    length_restriction_prompt = f"Please use about {cfg.TEXT_LENGTH_IN_WORDS_TO_SUMMARIZE} words"
    prompt = f"Summarize this text in the Russian language. " \
            f"Please keep the style and do not add any additional information. " \
            f"{length_restriction_prompt}: {text}"
    # list_models = genai.list_models()
    response = model.generate_content(
        # 'Выдели основное содержание текста: ' + text,
        prompt,
            # generation_config=genai.types.GenerationConfig(
            #         # max_output_tokens=50,
            #         # temperature=1.0,
            #         )
            )
    return response.text

if __name__ == "__main__":
    response = summarize("gemini-1.5-flash", "Write a story about a magic backpack.")
    print(response)