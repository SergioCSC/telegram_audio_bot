# -*- coding: utf-8 -*-

# Sample Python code for youtube.captions.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python


import tg

import yt_dlp
from yt_dlp.utils import DownloadError
from pytubefix import YouTube
# from pytube import YouTube
# from pytube.download_helper import (
#     download_videos_from_channels,
#     download_video,
#     download_videos_from_list,
# )
# from pytube.exceptions import PytubeError


# import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import os
import tempfile
import pathlib
from logging import error, warning, info, debug

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
NONAME = ''




def download_youtube_video(url, output_path="./"):
    try:
        # Create YouTube object
        youtube = YouTube(url)

        import pytube
        # Fix regex issue
        # pytube.extract.regex_search = lambda pattern, string, group: ""  # Override with no-op if regex fails
        
        # Get the highest resolution stream
        video_stream = youtube.streams.get_highest_resolution()

        print(f"Downloading: {youtube.title}...")

        # Download video
        video_stream.download(output_path)

        print(f"Download completed! Video saved to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

    


def download_audio_from_site(video_url: str, chat_id: int) -> tuple[bytes, str]:
    """
    Downloads the audio from a video URL and returns it as a bytes object.

    Args:
        video_url (str): The URL of the video to download audio from.

    Returns:
        bytes: The audio data as a bytes object.
    """

    warning('start')
    debug(f'{video_url = }')
    temp_dir = tempfile.gettempdir()

    ydl_opts = {
        'format': 'worstaudio',

        # 'format': 'bestaudio/best',
        # 'postprocessors': [{
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'mp3',
        #     'preferredquality': '192',
        # }],
        # 'outtmpl': '%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
        # 'quiet': True,  # Suppress console output
        'outtmpl': f'{temp_dir}/%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s',
        'logtostderr': True
    }
    try:
        yt = YouTube(video_url)
        audio_streams = yt.streams.filter(only_audio=True)
        stream = yt.streams.get_by_itag(139)
        audio_filename = stream.download()

    # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #     try:
    #         ydl.download([video_url])
    #         info_dict = ydl.extract_info(video_url, download = True)
    #         audio_filename = ydl.prepare_filename(info_dict)
    except DownloadError as e:
        error_message = f"Error downloading audio: {e}"
        error(error_message)
        tg.send_message(chat_id, error_message)
        return b'', ''

    if not audio_filename:
        error_message = f"Error downloading audio: {audio_filename}"
        error(error_message)
        tg.send_message(chat_id, error_message)
        return b'', ''

    with open(audio_filename, 'rb') as audio_file:
        mp4_audio_bytes = audio_file.read()  # TODO: mp4 ? really ?

    audio_file = pathlib.Path(audio_filename)
    if audio_file.exists():
        audio_file.unlink()
    
    return mp4_audio_bytes, audio_file.suffix


def download_subtitles(video_url: str, 
                       language: str ='ru', 
                       format: str ='json3') -> tuple[str, str]:
    
    # video = download_video(url="https://www.youtube.com/watch?v=EyxgV05oBwA")

    
    # YouTube('https://youtu.be/EyxgV05oBwA').streams.first().download()
    # yt = YouTube('https://youtu.be/EyxgV05oBwA')
    # result = yt.streams \
    #         .filter(progressive=True, file_extension='mp4') \
    #         .order_by('resolution') \
    #         .desc() \
    #         .first() \
    #         .download() \

    captions, name = _get_captions_dict_from_url(video_url)
    subtitles: dict = get_subtitles_from_captions(captions, language)
    
    if not subtitles:
        error_str = f"No subtitles available for the given video."
        error(error_str)
        return error_str, NONAME

    plain_text = get_plain_text_from_subtitles_dict(subtitles)
    
    # ydl_opts = {
    #     'writesubtitles': True,  # Enable downloading subtitles
    #     'writeautomaticsub': True,  # Fallback to auto-generated subtitles if manual are not available
    #     'skip_download': True,  # Skip downloading the video itself
    #     'subtitleslangs': [language],  # Specify the language of the subtitles
    #     'subtitlesformat': format,  # Specify the format of the subtitles
    # }

    # subtitles_dict = None
    # name: str = NONAME
    # # Custom downloader to capture subtitles in memory
    # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #     try:
    #         info = ydl.extract_info(video_url, download=False)
    #         subtitles = info.get('requested_subtitles')
    #         name: str = info.get('title', NONAME)
    #         if name:
    #             name = name.replace('/', '-')
    #             name += ' — subtitles'
            
    #         if subtitles and language in subtitles:
    #             url = subtitles[language]['url']
    #             # Fetch subtitle content from the URL
    #             response = requests.get(url)
    #             response.raise_for_status()
    #             subtitles_dict = response.json()
    #     except Exception as e:
    #         error_str = f"Error downloading subtitles: {e}"
    #         error(error_str)
    #         return error_str, name



    # Return the processed plain text
    return plain_text, name


def _get_captions_dict_from_url(video_url: str) -> tuple[dict, str]:
    try:
        yt = YouTube(video_url)
        name: str = yt.title
        if name:
            name = name.replace('/', '-')
            name += ' — subtitles'

        captions = yt.captions
        return captions, name
    except Exception as e:
        error_str = f"Error downloading subtitles: {e}"
        error(error_str)
        return {}, NONAME


def get_subtitles_from_captions(captions:dict, language: str = 'ru') -> dict:

    subtitles_dict = None
    if captions.get(language):
        subtitles_dict = captions.get(language, {}).json_captions
    elif captions.get('a.' + language):
        subtitles_dict = captions.get('a.' + language, {}).json_captions
    else:
        error_str = f"No subtitles available for the given video."
        error(error_str)
        return {}
    
    if not subtitles_dict:
        error_str = f"No subtitles available for the given video."
        error(error_str)
        return {}
    
    return subtitles_dict


def get_plain_text_from_subtitles_dict(subtitles_dict: dict) -> str:
    plain_text = ''

    for event in subtitles_dict.get('events', []):
        for seg in event.get('segs', []):
            word = seg.get('utf8', '')
            plain_text += word
        # start_time = event['tStartMs'] / 1000  # Convert milliseconds to seconds
        # end_time = (event['tStartMs'] + event['dDurationMs']) / 1000
        # print(f"[{start_time:.2f} -> {end_time:.2f}] {text}")
    
    return plain_text


# def main():
#     # Disable OAuthlib's HTTPS verification when running locally.
#     # *DO NOT* leave this option enabled in production.
#     os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#     api_service_name = "youtube"
#     api_version = "v3"
#     client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

#     # Get credentials and create an API client
#     flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
#         client_secrets_file, scopes)
#     credentials = flow.run_console()
#     youtube = googleapiclient.discovery.build(
#         api_service_name, api_version, credentials=credentials)

#     request = youtube.captions().list(
        
#     )
#     response = request.execute()

#     print(response)

if __name__ == "__main__":

    # main()

    video_url = input("Enter the YouTube video URL: ")
    output_directory = input("Enter the output directory (default is current directory): ") or "./"
    download_youtube_video(video_url, output_directory)