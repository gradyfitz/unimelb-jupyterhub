import os
import subprocess
import zipfile
import submitutils
import time
import datetime
import glob
import re
import markutils
import subprocess

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import json
import binascii

backup_loc = os.getenv("BACKUP_CLAIM_LOCATION")
user_loc = os.getenv("USER_CLAIM_LOCATION")
user_name = os.getenv("user")

USE_USERNAME_ONLY = True
OUTPUT_AS_USER_NAME = True

user_folder = user_loc
list_of_files = [file for file in submitutils.file_list(user_folder, recursive=True) if '.git' not in file['path']]

list_of_files.sort(key=lambda x: x['modified_s'], reverse=True)
list_of_filenames = [(file['filename'], file['timestamp'], file['raw_filesize']) for file in list_of_files]
if len(list_of_files) > 0:
    last_modified_file = list_of_files[0]
else:
    last_modified_file = {
        "timestampstring": "00000000000000"
    }
submission_zipfile_base = user_name + "_backup_" + last_modified_file['timestampstring']
submission_zipfile_name = submission_zipfile_base + ".zip"

print("[", datetime.datetime.now(), "]", "Storing files in zip file", submission_zipfile_name, "for submission.")
print("[", datetime.datetime.now(), "]", "Submission contents:")
print("\tFilename\tModified")
BOLD_START = "\033[1m"
END_FORMATTING = "\033[0m"
for file, modified, size in list_of_filenames:
    if modified == list_of_filenames[0][1]:
        print(BOLD_START, end="")
    print("\t" + file + "\t" + modified + "\t" + submitutils.get_friendly_size(size))
    if modified == list_of_filenames[0][1]:
        print(END_FORMATTING, end="")

BASE_FOLDER = backup_loc
submission_zipfile_folder = BASE_FOLDER
submission_zipfile_location = submission_zipfile_folder + "/" + submission_zipfile_name
print("[", datetime.datetime.now(), "]", "Checking if",  submission_zipfile_location, "already exists")
if os.path.exists(submission_zipfile_location):
    print("[", datetime.datetime.now(), "]", submission_zipfile_location, "already exists, no data.")
else:
    # Ensure the folder exists
    os.popen('mkdir -p {}'.format(submission_zipfile_folder)).read()
    with zipfile.ZipFile(submission_zipfile_location, mode="w", compression=zipfile.ZIP_LZMA) as zf:
        for file in list_of_files:
            zf.write(file['path'], arcname=file['relative_path'])

    zip_hash = submitutils.get_file_hash(submission_zipfile_location)
    print("[", datetime.datetime.now(), "]", "Zip file hash:", zip_hash)
    zip_hash_location = submission_zipfile_folder + "/" + submission_zipfile_base + ".sha1"
    with open(zip_hash_location, "w") as f:
        f.write(zip_hash)

# Build encrypted cleanup payload
payload = {
    "delete": os.getenv("user"),
    "job_id": os.getenv("JOB_ID")
}

with open(os.getenv("PRIVATE_SIGNING_KEY")) as f:
    key_file = f.read()
public_key = RSA.import_key(key_file)

print(json.dumps(payload))

encryptor = PKCS1_OAEP.new(public_key)
encrypted = encryptor.encrypt(bytes(json.dumps(payload), "UTF-8"))

cleanup_payload = binascii.hexlify(encrypted).decode("UTF-8")

notify = subprocess.Popen(["python", os.getenv("REDIS_NOTIFICATION_SCRIPT_LOCATION"), "archive", cleanup_payload],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(notify.stdout.read().decode())
print(notify.stderr.read().decode())