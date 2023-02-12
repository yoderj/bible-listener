# npm install -g npm@9.4.0
# npm i bootstrap@5.3.0-alpha1
# npm install -g npm@9.4.0

import threading
from flask import Flask
import record_audio
import transcribe_google
import compare_text

# Use as sparingly as possible!
DOMAIN = 'localhost:5000'

with open('recordings/main_text.txt') as file:
    MAIN_TEXT = file.read()

with open('recordings/skip_text1.txt') as file:
    SKIP_TEXT1 = file.read()

with open('recordings/skip_text2.txt') as file:
    SKIP_TEXT2 = file.read()

BLANK_TEXT = ''

NAMES_FILE = 'recordings/names.txt'


def read_names():
    names = {}
    with open(NAMES_FILE) as file:
        for line in file.read().split('\n'):
            if line:
                id, name = line.split('\t')
                names[id] = name
    return names


NAMES = read_names()

USER_ID = '2'

with open('recordings/reference.txt') as file:
    REFERENCE = file.read()
with open('recordings/pretty_reference.txt') as file:
    PRETTY_REFERENCE = file.read()
DEBUG = False


# TODO: Automate?
GCLOUD_LOGIN = False


def get_name(id):
    return NAMES[id]


def create_menu_bar():
    return """<div class="container">
    <header class="d-flex flex-wrap justify-content-center py-3 mb-4 border-bottom">
      <a href="/" class="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none">
        <svg class="bi me-2" width="40" height="32"><use xlink:href="#bootstrap"/></svg>
        <span class="fs-4">Bible Listener</span>
      </a>

      <ul class="nav nav-pills">
        <li class="nav-item"><a class="nav-link">""" + get_name(USER_ID) + """</a></li>
        <li class="nav-item"><a href="meditate" class="nav-link active" aria-current="page">Meditate</a></li>
        <li class="nav-item"><a href="skip" class="nav-link">Skip Even</a></li>
        <li class="nav-item"><a href="skip2" class="nav-link">Skip Odd</a></li>
        <li class="nav-item"><a href="blank" class="nav-link">Blank</a></li>
        <!--li class="nav-item"><a href="#" class="nav-link">Verses</a></li>
        <li class="nav-item"><a href="#" class="nav-link">History</a></li-->
      </ul>
    </header>
  </div>"""


def create_html_header(meta_line=''):
    return """<!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                """+meta_line+"""
                <title>Bible listener</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
              </head>
              <body>
                              <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>

  """


HEADER = create_html_header() + create_menu_bar()


def create_header(meta_line=''):
    return create_html_header(meta_line=meta_line) + create_menu_bar()


FOOTER = """
    </body>
    </html>
    """

POOL_TIME = 5  # Seconds

# variables that are accessible from anywhere
shared_thread_data = {'comparison':('','')}
# lock to control access to variable
data_lock = threading.Lock()
recording_thread = None

app = Flask(__name__)


@app.route("/")
def hello_world():
    name = get_name(USER_ID)
    return HEADER+"""
    <div class="px-4 py-5 my-5 text-center">
    <!--img class="d-block mx-auto mb-4" src="/docs/5.3/assets/brand/bootstrap-logo.svg" alt="" width="72" height="57"-->
    <h1 class="display-5 fw-bold">Meditate on a verse</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4">Welcome <b>"""+name+"""</b>!  Bible Listener is a tool to help you reflect on God's precious word.  
      God's word reminds us of how precious God is to His People.  He is our Creator, our Friend, our Savior, and our
      Guide.  As we speak his Word, it shapes our lives.  Want to get started?</p>
      <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
        <a href="meditate" type="button" class="btn btn-primary btn-lg px-4 gap-3">Meditate on """+PRETTY_REFERENCE+"""</a>
        <!--button type="button" class="btn btn-outline-secondary btn-lg px-4">Secondary</button-->
      </div>
    </div>
  </div>
              </body>
            </html>
            """


def create_meditate_text(verse_text,meditate_button,record_button):
    return ("""
    <div class="px-4 py-5 my-5 text-center">
    <!--img class="d-block mx-auto mb-4" src="/docs/5.3/assets/brand/bootstrap-logo.svg" alt="" width="72" height="57"-->
    <h1 class="display-5 fw-bold">"""+PRETTY_REFERENCE+"""</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4">Press <b>Record</b>, then read this verse aloud.  Reading the reference before and after 
      the verse helps you find this verse again later.</p>
      <p class="lead mb-4"><b>""" + verse_text +"""</b></p>
      <p class="lead mb-4"></p>""" +
            create_buttons(meditate_button, record_button)
    + "</div></div>")


def create_buttons(meditate_button, record_button, record_name="Record"):
    tmp = ("""<div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
     """
           + ("""
        <a href=\"""" + meditate_button + """" type="button" class="btn btn-outline-secondary btn-lg px-4 gap-3">Return to meditate on full text</a>"""
              if meditate_button else ""
              ) +
           """
             <a href=\"""" + record_button + """" type="button" class="btn btn-outline-primary btn-lg px-4 gap-3">"""+
                   record_name+"""</a>
      </div>""")
    return tmp


@app.route("/meditate")
def meditate():
    return HEADER + create_meditate_text(MAIN_TEXT,
                                         None,
                                         'record') + FOOTER


@app.route("/skip")
def skip():
    return HEADER + create_meditate_text(SKIP_TEXT1,
                                         'meditate',
                                         'skip_record') + FOOTER


@app.route("/skip2")
def skip2():
    return HEADER + create_meditate_text(SKIP_TEXT2,
                                         'meditate',
                                         'skip2_record') + FOOTER


@app.route("/blank")
def blank():
    return HEADER + create_meditate_text(BLANK_TEXT,
                                         'meditate',
                                         'blank_record') + FOOTER


def create_record_text(verse_text,meditate_button, record_button):
    return """
    <div class="px-4 py-5 my-5 text-center">
    <!--img class="d-block mx-auto mb-4" src="/docs/5.3/assets/brand/bootstrap-logo.svg" alt="" width="72" height="57"-->
    <h1 class="display-5 fw-bold">"""+PRETTY_REFERENCE+"""</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4"><b style="color:red;">Recording</b>. Read this verse aloud.  Reading the reference before and after 
      the verse helps you find this verse again later.</p>
      <p class="lead mb-4"><b>""" + verse_text +"""</b></p>
            """ + create_buttons(meditate_button, record_button, record_name="Stop") + "</div></div>"


def start_recording():
    with data_lock:
        shared_thread_data['continue'] = False
    global recording_thread
    if not recording_thread:
        with data_lock:
            if not recording_thread:
                recording_thread = threading.Thread(target=inner_record)
                recording_thread.start()


@app.route("/record")
def record():
    start_recording()
    return HEADER + create_record_text(MAIN_TEXT,None,"stop") + FOOTER


@app.route("/skip_record")
def skip_record():
    start_recording()
    return HEADER + create_record_text(SKIP_TEXT1,"meditate","skip_stop") + FOOTER


@app.route("/skip2_record")
def skip2_record():
    start_recording()
    return HEADER + create_record_text(SKIP_TEXT2,"meditate","skip2_stop") + FOOTER


@app.route("/blank_record")
def blank_record():
    start_recording()
    return HEADER + create_record_text(BLANK_TEXT,"meditate","blank_stop") + FOOTER


def create_stop_header(url='reflect'):
    return create_header(meta_line='<meta http-equiv="refresh" content="5;url=http://'+DOMAIN+'/'+url+'">')


def create_stop_text():
    return ("""
    <div class="px-4 py-5 my-5 text-center">
    <h1 class="display-5 fw-bold">"""+PRETTY_REFERENCE+"""</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4"><b>Recording complete.</b>. The recording is being transcribed and compared 
      with the scripture text.  You should be able to reflect on this verse in just a moment, if everything works!
      </p></div></div>""")


def stop_recording():
    print('Stopping recording.')
    global recording_thread
    if recording_thread:
        record_audio.stop_recording()
    else:
        print('Error: stop route called when no recording_thread active.')


@app.route("/stop")
def stop():
    stop_recording()
    return create_stop_header('reflect') + create_stop_text() + FOOTER


@app.route("/skip_stop")
def skip_stop():
    stop_recording()
    return create_stop_header('skip_reflect') + create_stop_text() + FOOTER


@app.route("/skip2_stop")
def skip2_stop():
    stop_recording()
    return create_stop_header('skip2_reflect') + create_stop_text() + FOOTER


@app.route("/blank_stop")
def blank_stop():
    stop_recording()
    return create_stop_header('blank_reflect') + create_stop_text() + FOOTER


def get_comparison():
    global recording_thread
    if recording_thread:
        recording_thread.join()
        recording_thread = None

    with data_lock:
        global shared_thread_data
        comparison = shared_thread_data['comparison']
    return comparison


def create_diff_text(results):
    marked_transcription, marked_scripture = results
    return """<p class="lead mb-4">Your transcription:</p>
      <p class="lead mb-4"><b>""" + marked_transcription + """</b></p>
      <p class="lead mb-4">Scripture:</p>
      <p class="lead mb-4"><b>""" + marked_scripture + """</b></p>"""


def create_reflect_text(comparison, meditate_button, record_button, record_name="Record"):
    return ("""
    <div class="px-4 py-5 my-5 text-center">
    <!--img class="d-block mx-auto mb-4" src="/docs/5.3/assets/brand/bootstrap-logo.svg" alt="" width="72" height="57"-->
    <h1 class="display-5 fw-bold">"""+PRETTY_REFERENCE+"""</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4"><b>Time to reflect!</b>.  Here is a transcription of what you said and the verse you are
      memorizing:</p>"""+
    create_diff_text(comparison) + create_buttons(meditate_button, record_button, record_name=record_name)+'</div></div>')


@app.route("/reflect")
def reflect():
    comparison = get_comparison()
    return create_header() + create_reflect_text(comparison,"meditate","skip", record_name="Skip words") + FOOTER


@app.route("/skip_reflect")
def skip_reflect():
    comparison = get_comparison()
    return create_header() + create_reflect_text(comparison,"meditate","skip2", record_name="Skip different words") + FOOTER


@app.route("/skip2_reflect")
def skip2_reflect():
    comparison = get_comparison()
    return create_header() + create_reflect_text(comparison,"meditate","blank", record_name="No prompt") + FOOTER


def create_congratulations_text(results):
    return ("""
    <div class="px-4 py-5 my-5 text-center">
    <!--img class="d-block mx-auto mb-4" src="/docs/5.3/assets/brand/bootstrap-logo.svg" alt="" width="72" height="57"-->
    <h1 class="display-5 fw-bold">"""+PRETTY_REFERENCE+"""</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4"><b>Recording complete.</b>. Here is a comparison of the transcription with the actual verse:</p>
      """+create_diff_text(results)
      +"""<p class="lead mb-4">Congratulations! You have meditated on this verse without prompts.  Now you can continue to meditate on it 
      throughout the day as much as you want!
      </div></div>""")


@app.route("/blank_reflect")
def blank_reflect():
    comparison = get_comparison()
    return create_header() + create_congratulations_text(comparison) + FOOTER


def inner_record():
    if DEBUG:
        transcription = 'This is a test for fun'
        reference_text = 'And this is another test'
        transcription = compare_text.normalize_punctuation(transcription)
        reference_text = compare_text.normalize_punctuation(reference_text)
        print(compare_text.show_diff(transcription.split(), reference_text.split()))
        marked_transcription,marked_scripture = compare_text.html_diff(transcription.split(), reference_text.split())
        shared_thread_data['comparison'] = marked_transcription,marked_scripture
    else:
        base, filename, path = record_audio.create_recording_filename(REFERENCE, USER_ID)
        print('Will save to ' + filename + ' once Ctl-C is pressed (or red square in PyCharm) TODO...')
        print("Recording the verse as you meditate")
        record_audio.record_to_file(path)
        print("done - result written to", path)

        transcribe_google.google_transcribe(base, local_dir=record_audio.RECORDINGS_PREFIX, gcloud_login=GCLOUD_LOGIN)
        compare_text.set_base(base)  # TODO: Convert module to object?

        with open(compare_text.REFERENCE_TEXT_FILE, 'r') as file:
            reference_text = file.read()

        transcription = compare_text.extract_transcript_from_json()

        transcription = compare_text.normalize_punctuation(transcription)
        reference_text = compare_text.normalize_punctuation(reference_text)
        print(compare_text.show_diff(transcription.split(), reference_text.split()))

        marked_transcription, marked_scripture = compare_text.html_diff(transcription.split(), reference_text.split())
        with data_lock:
            # shared_thread_data['comparison'] = compare_text.show_diff(transcription.split(), reference_text.split())
            shared_thread_data['comparison'] = marked_transcription,marked_scripture


if __name__ == '__main__':
    app.run()
