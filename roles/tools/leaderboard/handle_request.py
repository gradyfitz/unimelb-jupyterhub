"""
Borrows heavily from examples in
https://github.com/kubernetes-client/python/tree/master/examples
"""
import time
import sys
import os
import json
import subprocess

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from typing import Dict, Optional, Any

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import json
import binascii


def handle_leaderboard(job):
    assignment_folder = os.getenv("ASSIGNMENT_SETUP_FOLDER")
    assignment = job["assignment"]
    subprocess.run(['timeout', os.getenv("LEADERBOARD_TIMEOUT"), 'python',  os.path.join(
        assignment_folder, assignment, "leaderboard", "leaderboard.py"), json.dumps(job)])


def encode(payload: Dict[Any, Any]):
    # payload = {
    #     "backup": "gfitzpatrick",
    #     "job_id": 4
    # }
    # payload = {
    #     "delete": "gfitzpatrick",
    #     "job_id": 4
    # }
    # payload = {
    #     "delete_pvc": "gfitzpatrick",
    # }

    with open(os.getenv("PUBLIC_SIGNING_KEY")) as f:
        key_file = f.read()
    public_key = RSA.import_key(key_file)

    print(json.dumps(payload))

    encryptor = PKCS1_OAEP.new(public_key)
    encrypted = encryptor.encrypt(bytes(json.dumps(payload), "UTF-8"))

    wire_data = binascii.hexlify(encrypted).decode("UTF-8")

    return(wire_data)


def decode(input: str):
    bindata = binascii.unhexlify(bytes(input, "UTF-8"))

    with open(os.getenv("PRIVATE_SIGNING_KEY"), "r") as f:
        key_file = f.read()
    private_key = RSA.import_key(key_file)

    decryptor = PKCS1_OAEP.new(private_key)
    decrypted = decryptor.decrypt(bindata)

    decrypted_text = decrypted.decode("UTF-8")

    return(decrypted_text)


def determine_job_type(description: Dict[Any, Any]) -> Optional[str]:
    if "assignment" in description.keys():
        return "leaderboard"
    else:
        return None


job_id = list(sys.argv)[1]
encrypted_payload = list(sys.argv)[2]

# Decode job.
decoded_payload = decode(encrypted_payload)
# Note: This will fail if the value is not valid JSON.
job_json = json.loads(decoded_payload)

# Check whether job is for backup or completion of the backup.
job_type = determine_job_type(job_json)

if job_type == "leaderboard":
    handle_leaderboard(job_json)
