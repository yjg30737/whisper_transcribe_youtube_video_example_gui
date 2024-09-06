import os
import requests
import subprocess
from pathlib import Path

ffmpeg_path = 'ffmpeg/ffmpeg.exe'
os.environ["PATH"] += os.pathsep + os.path.join(os.path.dirname(__file__), os.path.dirname(ffmpeg_path))

from openai import OpenAI
from pydub import AudioSegment
from pytube import YouTube


def split_the_audio(audio_file_path, split_duration=600000):
    audio = AudioSegment.from_file(audio_file_path)
    split_audio = []
    dirname = Path(audio_file_path).parent
    for i, j in enumerate(range(0, len(audio), split_duration)):
        _audio = audio[j:j + split_duration]
        filename = os.path.join(dirname, f'split_audio_{i}.mp3')
        _audio.export(filename, format='mp3')
        split_audio.append(filename)

    return split_audio

class GPTTranscribeWrapper:
    def __init__(self, api_key=None, db_url='sqlite:///conv.db'):
        super().__init__()
        self._client = None
        # Initialize OpenAI client
        self._is_available = True if api_key else False
        if api_key and self._is_available:
            self.set_api(api_key)
        # self._db_handler = ''
        # self.init_db(db_url)

    def is_available(self):
        return self._is_available

    def set_api(self, api_key):
        self._api_key = api_key
        self._client = OpenAI(api_key=api_key)
        os.environ['OPENAI_API_KEY'] = api_key

    def request_and_set_api(self, api_key):
        try:
            response = requests.get('https://api.openai.com/v1/models', headers={'Authorization': f'Bearer {api_key}'})
            self._is_available = response.status_code == 200
            if self._is_available:
                self.set_api(api_key)
            return self._is_available
        except Exception as e:
            print(e)
            return False

    def transcribe_audio(self, audio_file_path, model='whisper-1', response_format=None, timestamp_granularities=None):
        args = {
            'model': model,
        }

        if response_format:
            args['response_format'] = response_format
        if timestamp_granularities:
            args['timestamp_granularities'] = timestamp_granularities

        result_obj_lst = []
        result_audio_file_paths = split_the_audio(audio_file_path)

        next_starting_point = 0
        for result_audio_file_path in result_audio_file_paths:
            result_obj = {}
            with open(result_audio_file_path, 'rb') as audio_file:
                args['file'] = audio_file
                # print(split_the_audio(audio_file_path))
                # Get format of the file
                # print(type(args['file']))

                transcription = self._client.audio.transcriptions.create(
                    **args,
                )

                segments = transcription.segments

                language = transcription.language
                result_obj['language'] = language

                duration = transcription.duration
                result_obj['duration'] = duration
                result_obj['segments'] = []

                for segment in segments:
                    # segment['start'], segment['end'] should be 0.00 format
                    segment_obj = {
                        'start': round(segment['start']+next_starting_point, 2),
                        'end': round(segment['end']+next_starting_point, 2),
                        'text': segment['text']
                    }
                    result_obj['segments'].append(segment_obj)
                next_starting_point = result_obj['segments'][-1]['end']
            result_obj_lst.append(result_obj)
            Path(result_audio_file_path).unlink(missing_ok=True)
        return result_obj_lst, result_audio_file_paths

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

# For someone who wants to transcribe a specific part of the video
def remove_trim(downloaded_file):
    """
        Trims a given video file from a specified start time for a certain duration and saves it as a new file.

        Args:
            downloaded_file (str): Path to the original video file.
            start_time (int): Start time for trimming (in seconds).
            duration (int): Duration of the video to trim (in seconds).

        Returns:
            str: Path to the trimmed video file.
    """
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


def convert_to_srt(original_filename, content):
    def seconds_to_srt_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    srt_content = ""
    for idx, line in enumerate(content):
        try:
            # Extract the time and text parts
            time_part = line.split("]")[0].replace("[", "").strip()
            start_time, end_time = map(float, time_part.split(" --> "))
            text = line.split("] ")[1].strip()

            # Convert the time to SRT format and add to the SRT content
            srt_content += f"{idx}\n"
            srt_content += f"{seconds_to_srt_time(start_time)} --> {seconds_to_srt_time(end_time)}\n"
            srt_content += f"{text}\n\n"
            print(f"Start time: {start_time}, End time: {end_time}, Text: {text}")
        except Exception as e:
            print(f"Error processing line {idx}: {line} - {e}")

    # Save as SRT file
    srt_filename = original_filename.replace(".mp4", ".srt")
    with open(srt_filename, 'w', encoding='utf-8') as file:
        file.write(srt_content)

# CUI usage

# wrapper = GPTTranscribeWrapper(api_key=API_KEY)

# filename = 'content/Microsoft (MSFT) Q4 2022 Earnings Call(filtered).mp4'
# print(wrapper.transcribe_audio(filename, response_format='verbose_json', timestamp_granularities=['segment']), end='\n\n')

# dirname = Path('examples')
# filenames = [str(file) for file in dirname.iterdir() if file.is_file()]
# for filename in filenames:
#     result_obj_lst, result_audio_file_paths = wrapper.transcribe_audio(filename, response_format='verbose_json', timestamp_granularities=['segment'])
#     for result_obj in result_obj_lst:
#         print(f"Transcription language: {result_obj['language']}")
#         print(f"Transcription duration: {result_obj['duration']}")
#         segments = result_obj['segments']
#         for segment in segments:
#             start = segment['start']
#             end = segment['end']
#             text = segment['text']
#             print(f"[{start} --> {end}] {text}")