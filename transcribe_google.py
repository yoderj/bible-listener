# Developer install from scratch:
#
# * Install Notepad++
# * Install Git for Windows from https://git-scm.com
# * Install latest Python. (Will probably work with Python 3.10 or 3.11. Works with Python 3.9.13
#   * Run as adminstrator. Have it add Python to path. Preferably set install location
#     to C:\Program Files\Python39, 310, 311, etc.
#
# Set up your Google cloud account.
# 
# * Create a Google cloud project using your primary Google (gmail) account.
# * Create a billable account. (credit card needed.)
#   * Google provides a good amount of free text transcription and cloud bucket storage,
#     so, for light usage, you will not be billed anything.
# * Create a service account.
# * Give your gmail account the role "Service Account Token Creator"
#   through the IAM console. This allows my account to create tokens
#   for the service account.
#   Details: https://stackoverflow.com/a/60555486/1048186
# * Create an s3 bucket.  BUCKET_NAME holds the name of this bucket. This will
#   temporarily hold recordings during transcription.
# * Enable text-to-speech for the project.
#   (It was necessary (after the first attempted failed) to
#    follow a link within the failure message to enable text-to-speech
#    for the project. This could likely also be done before the first failure.)
#
# * Use the Windows Powershell option to install Google Cloud. Install the bundled Python, the default.
#   https://cloud.google.com/sdk/docs/install
#
#   During the install, you have the option to run gcloud init. Do this, and select your Google cloud
#   project as part of doing this.
#
# Open cmd as an administrator.  Install this project's dependencies:
# "C:\Program Files\Python39\python.exe" -m pip install --upgrade pip
# pip install flask
# pip install requests
# pip install pyaudio
# 
# The current versions of these libraries are saved by pipreqs to requirements.txt:
# Flask==2.2.2      # Simple web-server that runs on localhost
# PyAudio==0.2.13   # Audio recording
# requests==2.28.2  # To make HTTP requests to Google cloud
#
# Create a recordings.txt sub-directory, and add these files to it:
# service_account.txt -- account@project-1234.iam.gserviceaccount.com
#  account -- your service account's name
#  project-1234 -- your Google cloud project's name
#  There should NOT be a newline at the end of this file.
# names.txt -- This is a tab-delimited file with two columns.
#  id -- a decimal int holding your user id.  Please ask Josiah Yoder for a unique ID if you choose 
#        not to simply act as "guest."
#  name -- Your name.  Simply your first name, currently.
#
#  The verse is currently hard-coded  
#  reference.txt -- the coded reference for the verse. This project uses one of three standard formats for references:
#   Coded Reference   --- Pretty reference
#   bookCH_VS         --- Book CH:VS
#   bookCH_VS1-VS2    --- Book CH:VS1-VS2
#   bookCH1_VS1-CH2_VS2 --- Book CH1:VS1 - CH2:VS2
#  where, for the coded reference:
#   book -- the three-letter code used by Blue-Letter Bible. Google "blb book" and look at the URL to find this.
#   CH -- the decimal chapter number
#   VS -- the decimal verse number.
#
#  For example, the coded reference jhn3_16 stands for John 3:16, and jhn1_1-21_25 stands for the entire book of John from the first verse (John 1:1)
#  to the last one (John 21:25)
#
#  Ranges are inclusive of both ends.  1co1:12-13 includes exactly two verses.
#
#  This file MUST NOT have a newline at the end of it.
#
# pretty_reference.txt -- The "pretty reference" is the standard text format for a reference.
#   This reference is included before and after the verse and I plan to eventually treat it specially
#   when doing comparisons.  For example John 1:1 - 21:25 is the pretty reference for the whole book of John.
#   This file MAY NOT have any newline at the end of it.
#
# 0-jhn3_16-niv1984.txt -- The reference text.  Eventually, all of the verse related files will
#  be derived from this one and the current reference.
#  This is the file holding the standard Biblical text for a verse.
#  It starts with the pretty reference, followed by a space, followed by the text itself, followed by another space and the pretty reference.
#  The format of the filename is:
#    id-reference-version.txt
#  where
#    id -- the user's id in decimal.
#    reference -- the coded reference as described above
#    version -- niv1984. This is the only version supported so far.
# I follow biblememory.com in allowing users to maintain their own verses in a variety of versions.
# Then minor edits to punctuation or even wording can be made if desired to blend various versions.
# This file MAY have newlines anywhere a space would occur in it.
#
# main_text.txt -- an exact copy of 0-jhn3_16-niv1984.txt
# skip_text1.txt -- The main text, but with every other word replaced with underscores.
#   I hope to auto-generate this soon, but I want to handle references properly first as they
#   will be treated specially when creating this file.
# skip_text2.txt
#   Identical to skip_text1.txt, but with the other verses blanked out.
# The skip_texts are used ONLY for display right now.  Eventually, I would like to record what prompts
#   were displayed while recording a verse.  But I would like to figure out a uniform way of doing this that is flexible
#   to the many forms of practice that meditators may use.

import os
import subprocess
import shutil
import requests
import json
import compare_text

import sys
import logging
logging.basicConfig(filename='log.txt',level=logging.DEBUG)
print('Redirecting stdout and stderr to log file.')
sys.stdout = open('log.txt','a')
sys.stderr = sys.stdout

with open('recordings/service_account.txt') as file:
    # The service_account_name is the name you give it.
    # The project_id is something like my-project-name-12345
    # service_account_name@project_id.iam.gserviceaccount.com
    SERVICE_ACCOUNT_EMAIL = file.read()

BUCKET_NAME = 'bible-voice'

LOCAL_DIR = 'recordings' # This is the standard name for the folder into which all data files, including recordings,
                         # are placed.
BASE = None  # eg. jhn3_16-20230214022714gmt


# When True, run the `gcloud auth login` system command,
# which will open a browser and ask you to confirm that you want to authenticate with your
# Google account.  Once authenticated, it lasts for a while (more than a day) before
# you need to do it again
# GCLOUD_LOGIN = True
GCLOUD_LOGIN = False


def google_transcribe(base, local_dir=None,gcloud_login=True):
    """
    :param base: The name of the file without the .wav extension
    :param local_dir: If provided, upload the file from this local_dir. Default: None
                      If not provided, assume that the file has already been uploaded.
    :param gcloud_login: If true, login through a popped-up web browser. (Can set to false
       after first call in an hour)
    """
    json_file = base + '.json'
    audio_file = base + '.wav'
    service_account = SERVICE_ACCOUNT_EMAIL
    if gcloud_login:
        print('Requesting access token')
        gcloud_exe_full_path = shutil.which('gcloud')
        print('gcloud path:',gcloud_exe_full_path)
        outcome = subprocess.run(gcloud_exe_full_path + ' auth login', capture_output=True)
        print(outcome.stdout.decode('utf-8'))
        print(outcome.stderr.decode('utf-8'))
    # The approach used here was recommended by this SO answer:
    # https://stackoverflow.com/a/60555486/1048186
    print('Requesting token for user account')
    user_access_token = subprocess.check_output(shutil.which('gcloud') + ' auth '
                                                                         'print-access-token')
    user_access_token = user_access_token.decode('ascii').strip()
    print('Requesting token for service account')
    response = requests.post('https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts'
                             '/' + service_account + ':generateAccessToken',
                             headers={'Content-Type': 'application/json',
                                      'Authorization': 'Bearer ' + user_access_token},
                             data="""{
                                  "delegates": [],
                                  "scope": [
                                      "https://www.googleapis.com/auth/cloud-platform"
                                  ],
                                  "lifetime": "3600s"}"""
                             )
    if response.status_code == 200:
        response_json = json.loads(response.text)
        expire_time = response_json['expireTime']
        service_access_token = response_json['accessToken']
    else:
        print('Could not get access token. Status code:', response.status_code)
        print('Message:', response.text)
        raise Exception('Could not get access token. Message:' + response.text)
    if local_dir or local_dir == '':
        upload_to_bucket(audio_file, local_dir, service_access_token)
    print('Requesting transcription')
    synchronous_recognize(audio_file, json_file, service_access_token)
    delete_bucket_object(audio_file,service_access_token)


def upload_to_bucket(audio_file, local_dir, service_access_token):
    print('Uploading audio')
    with open(local_dir + '/' + audio_file, 'rb') as file:
        audio_data = file.read()
    response = requests.post('https://storage.googleapis.com/upload/storage/v1/b/' + BUCKET_NAME +
                             '/o?uploadType=media&name=' + audio_file,
                             headers={'Content-Type': 'audio/wav',
                                      'Authorization': 'Bearer ' + service_access_token},
                             data=audio_data
                             )
    if response.status_code == 200:
        print('File successfully uploaded')
    else:
        print('Could not upload file.. Status code:', response.status_code)
        print('Message:', response.text)
        raise Exception('Could not upload file. Message:' + response.text)


def synchronous_recognize(audio_file, json_file, service_access_token):
    response = requests.post('https://speech.googleapis.com/v1p1beta1/speech:recognize',
                             headers={'Content-Type': 'application/json',
                                      'Authorization': 'Bearer ' + service_access_token},
                             data="""{
              "config": {
                "encoding": "LINEAR16",
                "languageCode": "en-US",
                "sampleRateHertz": 44100,
                "audioChannelCount": 1,
                "alternativeLanguageCodes": [],
                "profanityFilter": true,
                "speechContexts": [],
                "adaptation": {
                  "phraseSets": [],
                  "phraseSetReferences": [],
                  "customClasses": []
                },
                "enableWordTimeOffsets": true,
                "enableWordConfidence": true,
                "model": "video",
                "useEnhanced": true
              },
              "audio": {
                "uri": "gs://"""+BUCKET_NAME+'/' + audio_file + """"
              }
            }
            """
                             )
    if response.status_code == 200:
        filename = 'recordings/' + json_file
        print('Writing transcription to', filename)
        with open(filename, 'w') as file:
            file.write(response.text)
    else:
        print('Could not get transcription. Status code:', response.status_code)
        print('Message:', response.text)


def delete_bucket_object(audio_file, service_access_token):
    """
    Delete a file that was previously uploaded with upload_to_bucket()
    :param audio_file: The name of the file to delete. This should NOT have a path, just the filename and extension
    :param service_access_token: See google_transcribe for how to get this token.
    """
    print('Deleting '+audio_file+ ' from Google Cloud')
    print('https://storage.googleapis.com/upload/storage/v1/b/' + BUCKET_NAME +
                             '/o/'+audio_file)
    response = requests.delete('https://storage.googleapis.com/storage/v1/b/' + BUCKET_NAME +
                             '/o/'+audio_file,
                             headers={'Authorization': 'Bearer ' + service_access_token},
                             )
    if response.status_code == 204:
        print('File successfully deleted')
    else:
        print('Could not delete file.. Status code:', response.status_code)
        print('Message:', response.text)
        raise Exception('Could not delete file. Message:' + response.text)


if __name__ == '__main__':
    # def f():
    google_transcribe(BASE, local_dir=LOCAL_DIR, gcloud_login=GCLOUD_LOGIN) # Can set gcloud_login to False after first run of day.

    compare_text.set_base(BASE)  # TODO: Convert module to object.

    with open(compare_text.REFERENCE_TEXT_FILE, 'r') as file:
        reference_text = file.read()

    transcription = compare_text.extract_transcript_from_json()

    transcription = compare_text.normalize_punctuation(transcription)
    reference_text = compare_text.normalize_punctuation(reference_text)
    print(compare_text.show_diff(transcription.split(), reference_text.split()))


