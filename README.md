GUI Showcase of using Whisper to transcribe and analyze Youtube video

This GUI is based on this <a href="https://analyzingalpha.com/openai-whisper-python-tutorial">article</a>.

I refacotored a little and make it easier to understand :)

## Requirements (Package)
* PyQt5>=5.14
* pytube - to install youtube video as an audio
* openai-whisper - to extract the language and transcribe the content of the audio

## Requirements (Software)
* ffmpeg (you can install this with choco install ffmpeg in Windows and sudo apt-get ffmpeg in linux)

## How to Run
1. git clone ~
2. pip install -r requirements.txt
3. python main.py

## How it works
First, This app will download the Youtube video as 128kb audio file.

Then this app trim the audio file with ffmpeg. The term "trim" means to remove the opening and ending music or silent portions from a video.

ffmpeg command will be run consequently after audio is downloaded.

Finally this app will transcribe the audio as verbose format, stream the output and display it in a text browser.

I use <a href="https://www.youtube.com/watch?v=3haowENzdLo">this video file</a> as a sample. This is good sample video called "Microsoft (MSFT) Q4 2022 Earnings Call" which length is about 1 and a half hour

## Preview
![image](https://github.com/yjg30737/whisper_transcribe_youtube_video_example_gui/assets/55078043/37762c36-e3e9-44f5-9db3-336459ac2e4d)
