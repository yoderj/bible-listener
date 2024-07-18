import os
import re
import unicodedata
import difflib
import json


PATH = 'recordings/'


def set_base(base):
    global BASE
    global DATE_LENGTH
    global SHORTER_BASE
    global REFERENCE_TEXT_FILE
    global TRANSCRIPTION_JSON_FILE
    global TRANSCRIPTION_TEXT_FILE
    global AUDIO_FILE
    BASE = base
    DATE_LENGTH = 18 # Fixed by format
    assert BASE.rfind('-') == len(BASE)-DATE_LENGTH
    SHORTER_BASE = BASE[:-DATE_LENGTH]
    REFERENCE_TEXT_FILE = PATH+SHORTER_BASE+'-niv1984.txt'
    AUDIO_FILE = PATH + BASE + '.wav'
    TRANSCRIPTION_JSON_FILE = PATH + BASE + '.json'
    assert BASE # BASE cannot be an empty string to not overwrite the Scripture text.
    TRANSCRIPTION_TEXT_FILE = PATH + BASE + '.txt'

def normalize_punctuation(transcription):
    s = ''.join(c if unicodedata.category(c)[0] not in 'CSP' else ' ' for c in transcription)
    s = re.sub(' +', ' ', s)
    s = s.lower()
    return s


def show_diff(a,b):
        """Unify operations between two compared strings
    seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
        # https://stackoverflow.com/a/47617607/1048186
        matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
        def process_tag(tag, i1, i2, j1, j2):
            if tag == 'replace':
                return '{' + ' '.join(matcher.a[i1:i2]) + ' -> ' + ' '.join(matcher.b[j1:j2]) + '}'
            if tag == 'delete':
                return '{- ' + ' '.join(matcher.a[i1:i2]) + '}'
            if tag == 'equal':
                return ' '.join(matcher.a[i1:i2])
            if tag == 'insert':
                return '{+ ' + ' '.join(matcher.b[j1:j2]) + '}'
            assert False, "Unknown tag %r" % tag
        return ' '.join(process_tag(*t) for t in matcher.get_opcodes())


def html_diff(a, b):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    # https://stackoverflow.com/a/47617607/1048186
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)

    def tag_transcript(tag, i1, i2, j1, j2):
        if tag == 'replace':
            return '<span style = "color:goldenrod">'+(' '.join(matcher.a[i1:i2]))+'</span>'
        if tag == 'delete':
            return '<span style = "color:goldenrod">'+(' '.join(matcher.a[i1:i2]))+'</span>'
        if tag == 'equal':
            return ' '.join(matcher.a[i1:i2])
        if tag == 'insert':
            return ''
        assert False, "Unknown tag %r" % tag

    def tag_scripture(tag, i1, i2, j1, j2):
        if tag == 'replace':
            return '<span style = "color:green">'+(' '.join(matcher.b[j1:j2]))+'</span>'
        if tag == 'delete':
            return ''
        if tag == 'equal':
            return ' '.join(matcher.a[i1:i2])
        if tag == 'insert':
            return '<span style = "color:green">'+(' '.join(matcher.b[j1:j2]))+'</span>'
        assert False, "Unknown tag %r" % tag

    return (' '.join(tag_transcript(*t) for t in matcher.get_opcodes()),
            ' '.join(tag_scripture(*t) for t in matcher.get_opcodes()))


def extract_transcript_from_json():
    print('Compare text is working with ' + TRANSCRIPTION_JSON_FILE)
    with open(TRANSCRIPTION_JSON_FILE,
              'r') as file:
        dictionary = json.load(file)
    transcript = ''
    for result in dictionary['results']:
        for alternative in result['alternatives']:
            if 'transcript' in alternative:
                transcript += alternative['transcript']
    return transcript


def read_transcript_from_txt():
    print('Compare text is working with ' + TRANSCRIPTION_TEXT_FILE)
    with open(TRANSCRIPTION_TEXT_FILE,
              'r') as file:
        transcript = file.read()
    return transcript
# Other users


BASE = None  # This base is the full recording name without the final .wav or .json extension.
                                      # e.g., 5-jhn3_16-20230214022714gmt


if __name__ == '__main__':
# def f():
    set_base(BASE)

    # extract_transcript_from_json()

    with open(REFERENCE_TEXT_FILE, 'r') as file:
        reference_text = file.read()

    # with open(PLAINTEXT_TRANSCRIPTION_FILE, 'r') as file:
    #     transcription = file.read()
    # transcription = extract_transcript_from_json()
    transcription = read_transcript_from_txt()

    transcription = normalize_punctuation(transcription)
    reference_text = normalize_punctuation(reference_text)
    print(show_diff(transcription.split(), reference_text.split()))

# https://stackoverflow.com/a/7268456/1048186
pass