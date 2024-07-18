import threading
from sys import byteorder
from array import array
# https://stackoverflow.com/questions/892199/detect-record-audio-in-python
import pyaudio
import wave
import datetime

import transcribe_openai
import compare_text

RECORDINGS_PREFIX = 'recordings/'

MAX_PAUSE_IN_SILENT_BUFFERS = 880
REPORT_INTERVAL = 88
SILENCE_VOLUME_THRESHOLD = 300

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

# Time for an object?
continue_recording = True
recording_lock = threading.Lock()


def stop_recording():
    with recording_lock:
        global continue_recording
        continue_recording = False


def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < SILENCE_VOLUME_THRESHOLD


def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def trim(snd_data):
    """
    Trim the blank spots at the start and end
    """

    # TODO: Decide whether trimming is a feature or bug.
    # (sometimes it feels the beginning gets clipped off -- is this why?)
    def _trim(snd_data):
        snd_started = False
        r = array('h')
        for i in snd_data:
            if not snd_started and abs(i) > SILENCE_VOLUME_THRESHOLD:
                snd_started = True
            if snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data


def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    silence = [0] * int(seconds * RATE)
    r = array('h', silence)
    r.extend(snd_data)
    r.extend(silence)
    return r


def record():
    with recording_lock:
        global continue_recording
        continue_recording = True

    """
    Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure VLC et al can play
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    try:
        while continue_recording:
            # little endian, signed short
            snd_data = array('h', stream.read(CHUNK_SIZE))
            if byteorder == 'big':
                snd_data.byteswap()
            r.extend(snd_data)

            silent = is_silent(snd_data)

            if not snd_started and not silent:
                snd_started = True

            if silent and snd_started:
                num_silent += 1
            else:
                num_silent = 0

            if snd_started and num_silent > 0 and num_silent % REPORT_INTERVAL == 0:
                print('Silent:',num_silent,max(snd_data))

            if snd_started and num_silent > MAX_PAUSE_IN_SILENT_BUFFERS:
                print('Would normally stop recording at this point due to extended silence.')
                # break # Uncomment for silence to automatically break it.
                # TODO: Remove this option entirely?  Not really useful for this app?
    except KeyboardInterrupt:
        print('Interrupted while recording')
    except:
        print('Unknown exception while recording')

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r


def record_to_file(path):
    """Records from the microphone and outputs the resulting data to 'path'"""
    sample_width, data = record()
    data = data.tobytes()

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


def create_recording_filename(reference, user_id):
    timestamp = datetime.datetime.utcnow()
    base = str(user_id) + '-' + reference + timestamp.strftime('-%Y%m%d%H%M%Sgmt')
    filename = base + '.wav'
    path = RECORDINGS_PREFIX + filename
    return base, filename, path


BASE = None
# GCLOUD_LOGIN = True
GCLOUD_LOGIN = False


if __name__ == '__main__':
# def tmp(): # To enable PyCharm submethod extraction
    user_id = 0 # Guest -- Please contact Josiah Yoder for a globally-unique user id.
    print('Assuming User ID #'+str(user_id))
    reference = input('Please enter the Bible reference for your verse ('+str(BASE)+'): ')
    if not reference:
        reference = BASE
    base, filename, path = create_recording_filename(reference, user_id)
    print('Will save to '+filename+' once Ctl-C is pressed (or red square in PyCharm)')
    print("Please speak the reference, the verse, and the reference again. Then hit the cancel button. "
          "(Or red square in PyCharm)")
    record_to_file(path)
    print("done - result written to",path)

    # Can set gcloud_login=False after first run of the day.
    compare_text.set_base(base)  # TODO: Convert module to object.
    transcribe_openai.openai_transcribe()

    with open(compare_text.REFERENCE_TEXT_FILE, 'r') as file:
        reference_text = file.read()

    transcription = compare_text.extract_transcript_from_json()

    transcription = compare_text.normalize_punctuation(transcription)
    reference_text = compare_text.normalize_punctuation(reference_text)
    print(compare_text.show_diff(transcription.split(), reference_text.split()))

    pass
