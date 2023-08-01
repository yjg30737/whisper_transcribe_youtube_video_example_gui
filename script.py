import os
import subprocess

from pytube import YouTube

import whisper

model = whisper.load_model("base")

def install_audio(youtube_video_url):
    youtube_video_content = YouTube(youtube_video_url)

    directory = 'content'

    # filter only audio
    audio_streams = youtube_video_content.streams.filter(only_audio=True)

    # select 128kb stream
    audio_stream = audio_streams[1]

    # download it
    downloaded_file = audio_stream.download(directory)

    return downloaded_file

def remove_trim(downloaded_file):
    base_filename = os.path.splitext(os.path.basename(downloaded_file))[0]
    dst_filename = os.path.join(os.path.dirname(downloaded_file), f'{base_filename}(filtered).mp4')
    # trim file with ffmpeg
    ffmpeg_command = f'ffmpeg -ss 1924 -i "{downloaded_file}" -t 2515 "{dst_filename}"'
    try:
        subprocess.run(ffmpeg_command, shell=True, check=True)
        print("FFmpeg command executed successfully.")
        return dst_filename
    except subprocess.CalledProcessError as e:
        print("Error executing FFmpeg command:", e)
    return dst_filename

def transcribe_audio(dst_filename):
    result = model.transcribe(dst_filename, verbose=True)
    return result['text']