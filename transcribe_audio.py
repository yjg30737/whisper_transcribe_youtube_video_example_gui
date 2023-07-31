import whisper

model = whisper.load_model("base")

def transcribe_audio(dst_filename):
    result = model.transcribe(dst_filename, verbose=True)
    return result['text']