# pip install openai-whisper # Just for reference, see: https://github.com/openai/whisper
# Download scoop from: https://github.com/ScoopInstaller/Scoop
# scoop install ffmpeg # Have to restart PyCharm after installing this. pip install ffmpeg-python MIGHT also work.
# # download amount: 461M # "small" model 2GB "VRAM." This model worked on my MSOE laptop.
#

import whisper
import compare_text

import sys
import logging

def log_silently():
    logging.basicConfig(filename='log.txt',level=logging.DEBUG)
    print('Redirecting stdout and stderr to log file.')
    sys.stdout = open('log.txt','a')
    sys.stderr = sys.stdout


LOCAL_DIR = 'recordings'
BASE = '2-1pe3_8-20220927192709gmt' # None  #
model = None


def openai_transcribe():
    global model
    if not model:
        model = whisper.load_model("small")

    result = model.transcribe(compare_text.AUDIO_FILE)
    with open(compare_text.TRANSCRIPTION_TEXT_FILE,'w',encoding='utf-8') as file:
        file.write(result["text"])


if __name__ == '__main__':
    # def f():
    compare_text.set_base(BASE)  # TODO: Convert module to object.

    openai_transcribe()

    with open(compare_text.REFERENCE_TEXT_FILE, 'r',encoding='utf-8') as file:
        reference_text = file.read()

    transcription = compare_text.read_transcript_from_txt()

    transcription = compare_text.normalize_punctuation(transcription)
    reference_text = compare_text.normalize_punctuation(reference_text)
    print(compare_text.show_diff(transcription.split(), reference_text.split()))