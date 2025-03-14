
import pathlib
import config as cfg
import deepgram_conn
from mark_it_down import mark_it_down
import tg
import transcoder
import groq_conn
import gemini_conn
import openai_conn
from utils import _init_logging, _sizeof_fmt
import youtube_conn
from youtube_conn import NONAME
import hugging_face_conn as hf



# from dotenv import load_dotenv

import io
import os
import sys
import time
import httpx
import tempfile
import requests
import contextlib
from contextlib import redirect_stdout
import logging
from logging import error, warning, info, debug
from collections import namedtuple

SUCCESSFULL_RESPONSE = {'statusCode': 200, 'body': 'Success'}
UNSUCCESSFULL_RESPONSE = {'statusCode': 500, 'body': 'Failure'}
EMPTY_RESPONSE_STR = 'EMPTY_RESPONSE_STR'
MARK_IT_DOWN_EXTENSTIONS = ('.xlsx', '.docx', '.pptx', '.zip', '.html', '.xml', '.csv')

def _send_text(chat_id: int, 
               text: str,
               content_marker: str, 
               is_subtitles: bool = False) -> None:
    warning('start')
    if chat_id in (0, -1):
        error(f'{chat_id = }. {content_marker = }. {text = }')

    file_ext = '.' + content_marker.lower().split('.')[-1]
    if len(text) > cfg.TEXT_LENGTH_TO_SUMMARIZE \
            or is_subtitles \
            or file_ext == '.md':
        summary: str = _summarize(content_marker, chat_id, text)
        # summary = """Кризис Римской империи III века (235-285 гг.) характеризовался экономическим, социальным и политическим коллапсом.  Смерть Александра Севера в 235 г. ознаменовала начало "императорской чехарды" – смены 29 императоров, большинство из которых погибли насильственной смертью.  Период предшествовал гражданской войне 193-197 гг. и правлению династии Северов (193-235 гг.), характеризующейся "военной монархией".  Кризис разделился на три этапа. Первый (235-268 гг.) –  постоянные войны, налоговые перегрузки,  потеря ряда территорий (Дакия,  восточная Валахия).  Создана система дукатов – военных округов под командованием duces. Второй (кульминационный) этап (253-268 гг., правление Галлиена) – одновременные войны на нескольких фронтах (алеманны, франки, готы, персы),  дезинтеграция империи (Галльская империя, Пальмирское царство).  Галлиен провёл армейские реформы. Третий этап (268-285 гг.) – остановка варварских вторжений,  восстановление единства империи династией иллирийцев (Клавдий II, Аврелиан),  победы над внешними врагами.  Убийство Карина в 285 г. и приход Диоклетиана положили конец кризису и началу домината. Экономический спад проявлялся в аграризации, разрушении городов, упадке торговли и ремесла,  гиперинфляции из-за "порчи монет", переходе к натуральному обмену.  Послекризисное положение улучшилось частично, но общеимперский рынок был разрушен.\n"""
        tg.send_message(chat_id, summary)
        tg.send_doc(chat_id, content_marker, text)
    else:
        tg.send_message(chat_id, text)
    warning('finish')


def lambda_handler(event: dict, context) -> dict:
    _init_logging()
    warning('start')
    update_message: dict = tg.get_update_message(event)

    chat_id = int(update_message.get('chat', {}).get('id', 0))
    if not chat_id:
        error(f'{EMPTY_RESPONSE_STR}\n\n{chat_id = }\n\n{update_message = }')
        return UNSUCCESSFULL_RESPONSE

    result_text, name = _get_text_and_name(update_message)
    is_subtitles = False  # TODO _is_link(update_message)
    content_marker = name if name else _get_content_marker(update_message, result_text)
    _send_text(chat_id, result_text, content_marker, is_subtitles)

    warning('finish')
    return SUCCESSFULL_RESPONSE


def _startswith(s: str, templates: list[str]) -> str:
    s = s.lower()
    for t in templates:
        if s.startswith(t):
            return t
    return ''


def _correct_by_phrases(prompt: str, key_phrases: list[str], new_phrase: str) -> str:
    if key_phrase := _startswith(prompt, key_phrases):
        prompt = new_phrase + '\n\n' + prompt[len(key_phrase):]
        return prompt
    return ''


def _correct_prompt(prompt: str) -> str:
    key_phrases = ['correct:', 'corect:', 'исправь:', 'поправь:', 'правь:']
    if corrected_prompt := _correct_by_phrases(prompt, 
            key_phrases, 
            'Correct this text:'
            ):
        return corrected_prompt
    
    key_phrases = ['translate:', 'translation:', 'переведи:', 'перевод:']
    if corrected_prompt := _correct_by_phrases(prompt, 
            key_phrases, 
            'Translate text from standard English to Russian or vice versa:'
            ):
        return corrected_prompt
    
    return prompt


def _get_media_duration(message: dict) -> int:
    duration = message.get('audio', message.get('voice', \
            message.get('video', message.get('video_note', {})))) \
            .get('duration', -1)
    return duration


def _is_link(message: dict) -> bool:
        input_text = message.get('text')
        input_text = str(input_text).lower().strip()

        return input_text.startswith('https://')
                # 'https://youtu.be/',
                # 'https://www.youtu.be/',
                # 'https://youtube.com/',
                # 'https://www.youtube.com/'))


def _get_content_marker(message: dict, message_text: str = '') -> str:

    def _first_words(text: str, words: int = 5) -> str:
        return '_'.join(str(text).split(maxsplit=words)[:words])
    def _get_sender_user(message: dict) -> str:
        user = message.get('forward_origin', {}).get('sender_user', {})
        username = '@' + user.get('username') + '_' if user.get('username') else ''
        first_name = user.get('first_name') + '_' if user.get('first_name') else ''
        last_name = user.get('last_name') if user.get('last_name') else ''
        result = f'{username}{first_name}{last_name}'.strip().strip('_')
        if result:
            return result
        return message.get('forward_origin', {}).get('sender_user_name', '')

    sender = _get_sender_user(message)
    if audio_info := message.get('audio'):
        return f'{sender}_{audio_info.get('performer', '')}_{audio_info.get('title', '')}'
    if doc_filename := message.get('document',{}).get('file_name', ''):
        file_ext = '.' + doc_filename.lower().split('.')[-1]
        if file_ext in MARK_IT_DOWN_EXTENSTIONS:
            return f'{sender}_{doc_filename}.md'
        else:
            return f'{sender}_{doc_filename}'
    if caption := message.get('caption'):
        return f'{sender}_{_first_words(caption)}'
    if message.get('video') or message.get('video_note') or message.get('voice'):
        duration = _get_media_duration(message)
        return f'{sender}_{duration}_seconds'
    if message_text:
        return f'{sender}_{_first_words(message_text)}'
    duration = _get_media_duration(message)
    return f'{sender} Media duration: {duration} seconds'


@contextlib.contextmanager
def silence():
    sys.stderr, old = io.StringIO(), sys.stderr
    try:
        yield
    finally:
        sys.stderr = old


def _get_audio_bytes_from_tg(media_url: str, message: dict) -> tuple[bytes, str]:
    response = requests.get(media_url)
    if message.get('video') or message.get('video_note') \
            or 'video' in message.get('document', {}).get('mime_type', ''):
        video_ext = message.get('video', message.get('document', {})) \
                .get('mime_type', '')
        video_ext = '.' + video_ext.split('/')[1] if video_ext else ''
        if not video_ext:
            if message.get('video_note'):
                video_ext = '.mp4'
            else:
                warning(f'unknown video type. {message = }')
        audio_bytes = transcoder.extract_mp3_from_video(response.content, video_ext)
        audio_ext = '.mp3'
    else:
        audio_bytes = response.content
        audio_ext = message.get('audio', message.get('voice', message.get('document', {}))) \
                .get('mime_type', '')
        audio_ext = '.' + audio_ext.split('/')[1] if audio_ext else ''
        if not audio_ext:
            warning(f'unknown audio type. {message = }')
            audio_ext = '.mp3'

    return audio_bytes, audio_ext


def _get_text_from_audio(audio_bytes: bytes, audio_ext: str, 
                         chat_id: int, content_marker: str) -> tuple[str, str]:
    
    output_text, model_name = groq_conn.transcribe_audio(
            audio_bytes, 
            audio_ext,
            chat_id,
            content_marker
    )

    if not output_text:
        output_text, model_name = deepgram_conn.transcribe_audio(
                audio_bytes, 
                audio_ext, 
                chat_id, 
                content_marker
        )

    return output_text, model_name
    

def _get_text_from_media(message: dict, chat_id: int) -> str:
    start_time = time.time()
    warning('start')
    debug(f'{message = }')
    
    content_marker = _get_content_marker(message)

    tg.send_message(chat_id, f'{content_marker} \
                    \n\nGetting media from Telegram ...')
    media_url, media_size = tg.get_media_url_and_size(message, chat_id)
    if not media_url:
        return ''
    
    if media_size > cfg.MAX_MEDIA_SIZE:
        output_text = f'{content_marker}\n\nToo big media file ({_sizeof_fmt(media_size)}).'
    elif False: #_get_media_duration(message) > cfg.MEDIA_DURATION_TO_USE_SPACE:
       pass

    else:
        audio_bytes, audio_ext = _get_audio_bytes_from_tg(media_url=media_url, message=message)
        output_text, model_name = _get_text_from_audio(audio_bytes=audio_bytes,
                                           audio_ext=audio_ext,
                                           chat_id=chat_id,
                                           content_marker=content_marker,
                                           )
    output_text = f"{content_marker}\nModel: {model_name}" \
            f"\n\nText: {output_text}" \
            f"\n\nCalc time: {int(time.time() - start_time)} seconds"

    return output_text


def _summarize(message_marker: str, chat_id: int, text: str) -> str:

    warning('start')
    debug(f'{text = }')
    chat_message = f'{message_marker}\n\nSending the text to Gemini for summarization ...'
    tg.send_message(chat_id, chat_message)
    # output_text = hf.summarize(cfg.HUGGING_FACE_TEXT_MODEL,
    #                            text=text)  #, chat_temp=0)
    output_text = gemini_conn.summarize(chat_id, text=text)
    debug(f'{output_text = }')
    warning('finish')
    return output_text


def _recognize(message_marker: str, chat_id: int, 
               mime_type: str, file_ext: str, file_bytes: bytes) -> str:

    warning('start')
    chat_message = f'{message_marker}\n\nSending the {file_ext} file to Gemini for recognition ...'
    tg.send_message(chat_id, chat_message)
    output_text = gemini_conn.recognize(chat_id, mime_type=mime_type, file_ext=file_ext, file_bytes=file_bytes)
    debug(f'{output_text = }')
    warning('finish')
    return output_text


def _get_text_and_name(message: dict, chat_temp: float = 1) -> tuple[str, str]:
    
    if not message:
        error(f'{EMPTY_RESPONSE_STR}')
        return EMPTY_RESPONSE_STR, NONAME
    
    chat_id = int(message.get('chat', {}).get('id', 0))
    if not chat_id:
        error(f'{EMPTY_RESPONSE_STR}\n\n{chat_id = }\n\n{message = }')
        return EMPTY_RESPONSE_STR, NONAME

    tg_chat_username = message.get('chat', {}).get('username', None)
    if tg_chat_username not in cfg.PERMITTED_TG_CHAT_USERNAMES:
        error_message = f'WRONG_TG_CHAT_USERNAME:\n\n{chat_id = }\n\n{tg_chat_username = }\n\n{message = }'
        error(error_message)
        return error_message, NONAME
    
    mime_type: str = message.get('document', {}).get('mime_type', '')
    if message.get('photo'):
        mime_type = 'image/jpeg'
    
    message_marker = _get_content_marker(message)
    input_text = message.get('text')
    input_text = str(input_text).strip()
    name = NONAME

    # or message.get('voice') \ voice is not supported because of potential privacy issues
    if message.get('audio') \
            or message.get('video') or message.get('video_note') \
            or 'video' in mime_type \
            or 'audio' in mime_type:

        output_text = _get_text_from_media(message=message, chat_id=chat_id)

    # TODO: don't recognize text files (.txt, .log, .py, .csv): just summarize them
    elif 'application/' in mime_type \
            or 'text/' in mime_type \
            or 'image/' in mime_type \
            or message.get('photo'):
        
        file_name = message.get('document', {}).get('file_name', 'image.jpg')
        file_ext = '.' + file_name.split('.')[-1] if len(file_name.split('.')) > 1 else ''
        file_url, file_size = tg.get_media_url_and_size(message, chat_id)
        response = requests.get(file_url)
        file_bytes = response.content
        
        if file_ext in MARK_IT_DOWN_EXTENSTIONS:
            output_text = mark_it_down(file_bytes, file_ext)
        else:
            output_text = _recognize(message_marker, chat_id, mime_type=mime_type, 
                                 file_ext=file_ext, file_bytes=file_bytes)

    elif input_text:
        if input_text == '/start':
            output_text = tg.get_bot_description(chat_id)
        elif _is_link(message):
            url = input_text.split()[0]
            output_text, name = youtube_conn.download_subtitles(video_url=url)
            if name == NONAME:
                audio_bytes, audio_ext = youtube_conn.download_audio_from_site(url, chat_id)
                if not audio_bytes:
                    response = requests.get(url)
                    conent_type = response.headers.get('content-type', '')
                    if conent_type.startswith('text/html'):
                        file_bytes = response.content
                        file_ext = '.html'
                        output_text = mark_it_down(file_bytes, file_ext)
                        # output_text = _recognize(message_marker, chat_id, mime_type=conent_type, 
                        #         file_ext=file_ext, file_bytes=file_bytes)
                    else:
                        # output_text = _summarize(input_text, message_marker, chat_id)
                        return '', NONAME
                else:
                    output_text, model_name = _get_text_from_audio(audio_bytes=audio_bytes,
                            audio_ext=audio_ext,
                            chat_id=chat_id,
                            content_marker=message_marker)
        else:
            tg.send_message(chat_id, 'I have to think about it. Just a moment ...')
            input_text = _correct_prompt(input_text)
            output_text = _summarize(input_text, message_marker, chat_id)

    else:
        error_message = f"Can't parse this type of Telegram message: {message}"
        error(error_message)
        output_text = "It seems I can't do what you want. \
                I can answer to text and transcribe audio into text."
        output_text += '\n\n' + error_message        

    debug(f'{output_text = }')
    warning('finish')
    return output_text, name


def telegram_long_polling():
    _init_logging()
    logging.getLogger().setLevel(cfg.LOG_LEVEL)  # for local run
    warning('start')
    tg.delete_webhook()
    time.sleep(1)
    
    timeout = 60
    offset = -2
    while True:
        start_time = time.time()
        url = f'{tg.TELEGRAM_BOT_API_PREFIX}{cfg.TELEGRAM_BOT_TOKEN}' \
                f'/getUpdates?offset={offset + 1}&timeout={timeout}'
        updates = requests.get(url).json()

        if updates['result']:
            for result in updates.get('result', []):
                offset = result.get('update_id', offset)
                message = result.get('message', {})
                chat_id = int(message.get('chat', {}).get('id', 0))
                if not chat_id:
                    error(f'{EMPTY_RESPONSE_STR}\n\n{chat_id = }\n\n{message = }')
                    continue

                # result_text = '''Automatic summarization is the process of shortening a set of data computationally, to create a subset (a summary) that represents the most important or relevant information within the original content. Artificial intelligence algorithms are commonly developed and employed to achieve this, specialized for different types of data. Text summarization is usually implemented by natural language processing methods, designed to locate the most informative sentences in a given document.[1] On the other hand, visual content can be summarized using computer vision algorithms. Image summarization is the subject of ongoing research; existing approaches typically attempt to display the most representative images from a given image collection, or generate a video that only includes the most important content from the entire collection.[2][3][4] Video summarization algorithms identify and extract from the original video content the most important frames (key-frames), and/or the most important video segments (key-shots), normally in a temporally ordered fashion.[5][6][7][8] Video summaries simply retain a carefully selected subset of the original video frames and, therefore, are not identical to the output of video synopsis algorithms, where new video frames are being synthesized based on the original video content.'''
                # result_text = """Кризис Римской империи III века — период в истории Древнего Рима, хронологические рамки которого обычно определяют в годы между гибелью Александра Севера в ходе мятежа солдат 19 марта 235 года и убийством императора Карина после битвы при Марге в июле 285 года. Этот период характеризуется рядом кризисных явлений в экономике, ремесле, торговле, а также нестабильностью государственной структуры, внутренними и внешними военными столкновениями и временной потерей контроля Рима над рядом областей. В различных исторических школах взгляды на причины возникновения кризисных явлений различаются, в том числе существует мнение об отсутствии необходимости выделять III век в качестве отдельного периода римской истории.\n\nПредкризисный этап\n\nПосле убийства последнего императора из династии Антонинов — Коммода, в Империи начинается гражданская война 193—197 годов. Ряд видных лидеров провозглашают себя императорами: Пертинакс и Дидий Юлиан в Риме, командующий дунайской армией Септимий Север, командующий сирийскими легионами Песценний Нигер и Клодий Альбин в Британии. Императорская власть была официально вручена сенатом вышедшему из войны победителем Септимию Северу, который основал императорскую династию Северов (193-235 гг.). Большинство историков считает политический режим при династии Северов «военной» или «солдатской» монархией. Увеличение степени политического участия армии, уровня её самостоятельности в своих политических интересах связано с рядом рубежных тенденций и моментов в самой военной организации, в частности, с активными мероприятиями и преобразованиями Септимия Севера, значительно уклонившегося от традиционного вектора военной политики, а также заложившего основы позднеантичной армии. Септимий опирался исключительно на армию, а режим правления при нём превратился в военно-бюрократическую монархию. Внешняя политика характеризовалась рядом успешных войн с Парфией (195-199 гг.) и с племенами каледонцев (208-211 гг.). После смерти императора его сын Антонин Каракалла (211-217 гг.) убил своего брата Гету, занял престол, после чего начал неоправданную войну с парфянами и был убит заговорщиками. Его преемник префект претория Макрин (11 апреля 217-218 гг.) совершил неудачный поход против парфян, с которыми был заключён невыгодный для римлян мир. Войско было недовольно Макрином; к тому же его азиатские привычки и изнеженность возбуждали всеобщее порицание. Тётке Каракаллы, Юлии Мезе, и двум дочерям её удалось расположить войско к юному Бассиану (Гелиогабалу), который и был провозглашён императором; Меза выдавала его за внебрачного сына Каракаллы. Макрин выслал против него Ульпия Юлиана, но солдаты убили последнего, и всё войско, кроме преторианцев, перешло на сторону Бассиана. Произошла битва при Антиохии, но Макрин, не дождавшись её исхода, обратился в бегство и вскоре был убит. После Макрина правителем Римской империи стал Гелиогабал (Элагабал, Бассиан, 218-222 гг.), в марте 222 года убитый своими воинами. Императором стал 13-летний Александр Север (222-235 гг.), при котором обострился финансовый кризис, а также повысилась угроза со стороны набиравшего мощь Новоперсидского царства, с которым в 231 году началась война. Александр был убит взбунтовавшимися легионерами, что ознаменовало начало ещё более глубокого политического и социально-экономического кризиса.\n\nПервый этап кризиса\n\nС 235 года начался период «императорской чехарды», империю сотрясали военные столкновения между претендентами на этот пост, а для снабжения противостоящих армий вводились чрезвычайные налоговые сборы. Между 235 и 268 годами было провозглашено 29 императоров (включая узурпаторов) и лишь 1 из них, Гостилиан, умер ненасильственной смертью (от чумы). 238 год получил известность как год шести императоров из-за быстро сменявших друг друга претендентов. В конечном итоге преторианцы провозгласили императором 13-летнего Гордиана (238-242), правление которого продолжалось несколько лет и было относительно успешным, однако юный император погиб во время похода против персов (вероятно, в результате интриг). Его преемники Филипп | Араб (244-249 гг.) и Деций Траян (249-251 гг.) ещё удерживали ситуацию под контролем, несмотря на борьбу друг с другом, подавление военных мятежей и войны с внешними противниками. Гибель Деция во время битвы с готами, в которой римляне потерпели сокрушительное поражение, ознаменовала углубление кризиса. Общей тенденцией первого периода кризиса стало то, что римляне постепенно начинают оставлять ряд территорий, что предполагало крайне негативные последствия. Так, римляне начинают уход в 240-е гг. из Дакии, из восточной части равнины Валахии они ушли уже к 242 г. Это поспособствовало тому, что римское влияние на северном побережье Чёрного моря было подорвано. К началу 40-х годов III в. правители империи пошли на объединение военных сил нескольких провинций, которые ставились под командование единого военачальника — duces. Военные округа (дукаты) делили вооружённые силы на группировки, основными из которых стали британская, восточная, дунайская, рейнская и африканская. В ряде случаев эти группировки выдвигали претендентов на императорский трон, боровшихся друг с другом. Система дукатов в составе Римской империи стала основным изменением в армии не только в первый период кризиса, но и, по сути, в рамках всего III в. н. э.\n\nВторой этап кризиса\n\nВторой этап кризиса, ставший кульминационным, характеризуется уже непрерывными войнами, ведущимися одновременно с несколькими противниками. В этот период правил Галлиен (253-268 гг.). При этом император, который находился во главе центральной власти, вынужден был как отражать атаки внешних врагов, так и бороться с римскими войсками, поддерживавшими узурпаторов. Западная часть империи страдала от постоянных вторжений алеманнов и франков, причём первые в своих набегах сумели проникнуть даже в Италию, а последние опустошали римскую территорию вплоть до Южной Испании; морское побережье разорялось саксами, а маркоманам удалось добиться от Галлиена уступки части Верхней Паннонии. Не меньший ущерб потерпели и восточные провинции государства от вторжений готов, персов и других народностей. На этом этапе происходит процесс дезинтеграции империи, когда отпадают Галльская империя и Пальмирское царство. Галлиеном были предприняты решительные шаги по реформированию не только армии, но и отчасти системы управления. Хотя ему не удалось решить все стоявшие перед ним проблемы, однако в результате его реформ, которые не затрагивали основы римской военной организации, но существенно модифицировали её, была создана более мобильная армия, способная своевременно реагировать на внешние и внутренние угрозы.\n\nТретий этап кризиса\n\nЗаключительный этап кризиса характеризуется тем, что римляне смогли остановить основные потоки варварских вторжений. К тому же преемникам Галлиена, отчасти используя некоторые его наработки, удалось стабилизировать положение на границах, остановить дезинтеграционные процессы и даже восстановить единство империи. Пришедшая к власти «династия иллирийцев» ознаменовала собой постепенный вывод Рима из кризиса. Клавдий II Готский (268-270 гг.) положил начало возрождению империи, разбив готов в битве при Нише и передав престол в руки Луция Домиция Аврелиана (270-275 гг.). Аврелиан отразил нашествие германских племён (впервые вторгшихся в Италию), восстановил римскую администрацию в восточных провинциях и подчинил Пальмирское царство и Галльскую империю. Пришедший к власти после очередной смуты Марк Аврелий Кар (282-283 гг.) разбил германцев, одержал победы над персами, но умер в августе 283 года. Его преемниками стали его сыновья Нумериан и Карин, ставшие соправителями. Но спустя год Нумериан во время очередной римско-персидской войны заболел и скончался (по другим данным убит) 20 ноября 284 года. После его смерти начальники войска провозгласили императором иллирийца Диокла, позднее известного под именем Диоклетиана, несмотря на то, что ещё был жив второй соправитель Карин, который пребывал в то время в Британии. После смерти отца и брата Карин выступил против провозглашения восточными легионами императором Диоклетиана, но в генеральном сражении в долине р. Марг (совр. Морава в Мёзии) потерпел поражение и был убит в июле 285 года. При Диоклетиане, который в течение 20-летнего правления почти не посещал Рим, наводя порядок в различных частях государства, империя укрепилась и ситуация относительно стабилизировалась примерно на 100 лет. Приход к власти Диоклетиана ознаменовал начало периода домината.\n\nЭкономический кризис\n\nЕщё в предкризисный период началась аграризация общества, шло сокращение числа мелких и средних собственников на фоне роста крупных латифундий. В дальнейшем в результате боевых действий ряд городов были разрушены, а торговля и ремёсла пришли в упадок. Кроме того, необходимость защищать границы от вторжений германских племён и персидской армии вынудила императоров чрезмерно расширить армию, расходы на содержание которой возросли, и римская экономика не могла их вынести. Чтобы поддерживать систему снабжения армии, императоры налагали огромное фискальное бремя на население и восполняли пробелы в казне через так называемую «порчу монет», то есть выпуск монеты, в которой вместо драгоценных содержалась большая примесь недрагоценных металлов. «Порча монет» привела к гиперинфляции. С другой стороны, налоговые органы не хотели собирать налоги в ставшей бесполезной монете, а вместо этого перешли к натуральному налогу (в продуктах). В результате экономика империи была в значительной степени возвращена в состояние товарной экономики. В свою очередь это вызвало упадок городов, особенно в западной части империи, кризис сильнее всего ударил по наиболее цивилизованным и романизированным областям. В послекризисный период экономическое положение несколько улучшилось, но в целом экономика так и не восстановилась. Общеимперский рынок, созданный в I—II веках нашей эры, был практически разрушен. Налицо был общий упадок сельского хозяйства, ремесла и индустрии, ухудшение безопасности на дорогах, рост экономического, а как следствие этого — и политического сепаратизма.\n"""
                result_text, name = _get_text_and_name(message)
                is_subtitles = False  # TODO _is_link(update_message)
                content_marker = name if name else _get_content_marker(message, result_text)
                _send_text(chat_id, result_text, content_marker, is_subtitles)
        end_time = time.time()
        warning(f'time between requests to Telegram Bot API: {end_time - start_time}')


def main():
    # # sys.stdout = sys.__stdout__
    # # sys.stderr = sys.__stderr__
    
    try:
        telegram_long_polling()
    except KeyboardInterrupt as e:
        tg.set_webhook()
        raise e
    pass


if __name__ == '__main__':
    # download_audio('https://youtu.be/EyxgV05oBwA?si=8pt3BVtC152O9GjG')
    # download_subtitles('https://youtu.be/EyxgV05oBwA?si=8pt3BVtC152O9GjG')

    # tg.set_webhook()
    main()
