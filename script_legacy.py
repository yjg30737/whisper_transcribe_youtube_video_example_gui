# Need to install numpy<2
# If you already have it, you have to downgrade.

import whisper
from pytube import YouTube

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

def transcribe_audio(dst_filename):
    result = model.transcribe(dst_filename, verbose=True)
    return result['text']