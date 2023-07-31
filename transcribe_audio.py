from script import transcribe_audio


if __name__ == '__main__':
    import sys
    dst_filename = sys.argv[1]
    transcribe_audio(dst_filename)