# Create a service account.
# It was necessary (after the first attempted failed) to
# follow a link within the failure message to enable text-to-speech
# for the project. This could likely also be done before the first failure.

# It was necessary to give my gmail account the role "Service Account Token Creator"
# through the IAM console. This allows my account to create tokens
# for the service account.
# Details: https://stackoverflow.com/a/60555486/1048186
#
# During the install, you have the option to run gcloud init. Do this, and select your Google cloud
# project as part of doing this.

# Install the gcloud cli (follow Windows instructions
# for powershell)
# https://cloud.google.com/sdk/docs/install
#
# Don't install Python during this install. Then the system Python will be used.
# But I find it necessary to set the CLOUDSDK_PYTHON
# environment variable to point at the system Python as done
# below.

# https://stackoverflow.com/a/54836800/1048186
# pip install --upgrade google-cloud-texttospeech
# pip install --upgrade google-cloud-storage

import os
import subprocess
import shutil
import requests
import json
import compare_text

os.environ['CLOUDSDK_PYTHON'] = 'python'

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


