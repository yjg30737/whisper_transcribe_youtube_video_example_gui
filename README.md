GUI Showcase of using Whisper to transcribe and analyze Youtube video

This GUI is based on this <a href="https://analyzingalpha.com/openai-whisper-python-tutorial">article</a>. But this article is quite old in 2024.

So i've changed a lot!

## Requirements (Package)
* PyQt5>=5.14
* openai
* python-docx
* psutil
* pytube - to install youtube video as an audio
* pydub
* requests
### Legacy
* openai-whisper - to extract the language and transcribe the content of the audio
* numpy<2.0.0

## Requirements (Software)
* ffmpeg (you can install this with choco install ffmpeg in Windows and sudo apt-get ffmpeg in linux)
- Actually the app includes ffmpeg.exe, so you don't need to download this.

## How to Run
1. git clone ~
2. pip install -r requirements.txt
3. python main.py

### You have to do this if you already have the same exact Youtube video !
![image](https://github.com/yjg30737/whisper_transcribe_youtube_video_example_gui/assets/55078043/9c4f0d88-c3ec-41cf-9c26-aadb9ef628fc)

## How it works
First, This app will download the Youtube video as 128kb audio file.

Then this app trim the audio file with ffmpeg. The term "trim" means to remove the opening and ending music or silent portions from a video.

ffmpeg command will be run consequently after audio is downloaded.

Finally this app will transcribe the audio as verbose format, stream the output and display it in a text browser.

I use <a href="https://www.youtube.com/watch?v=3haowENzdLo">this video file</a> as a sample. This is good sample video called "Microsoft (MSFT) Q4 2022 Earnings Call" which length is about 1 and a half hour

## Preview
### New version
![image](https://github.com/yjg30737/whisper_transcribe_youtube_video_example_gui/assets/55078043/96b8d19f-a95d-4d8b-a861-d09a632fad57)

### Legacy
It only works in CUI for some reasons.
