"""
Borrows heavily from examples in
https://github.com/kubernetes-client/python/tree/master/examples
"""
import time
import sys, os
import json

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

def launch_backup_job(name_long=None, user=None, job_id=None, core_v1=None):
    backup_location = os.getenv("BACKUP_CLAIM_NAME")
    backup_mount_location = os.getenv("BACKUP_CLAIM_LOCATION")
    user_mount_location = os.getenv("USER_CLAIM_LOCATION")
    image = os.getenv("ARCHIVE_IMAGE")
    volumes = [{
        "name": "user",
        "persistentVolumeClaim":
            {"claimName": "claim-{}".format(user)}
    }, {
        "name": "backup",
        "persistentVolumeClaim":
            {"claimName": backup_location}
    }, {
        "name": "public-rsa-key",
        "secret": {
            "secretName": "ass-rsa-public"
        }
    }]
    volume_mounts = [{
        "name": "user",
        "mountPath": user_mount_location
    }, {
        "name": "backup",
        "mountPath": backup_mount_location
    }, {
        "name": "public-rsa-key",
        "mountPath": "/etc/signing/public"
    }]
    env = [{
        "name": "JOB_ID",
        "value": job_id
    }, {
        "name": "user",
        "value": user
    }, {
        "name": "BACKUP_CLAIM_LOCATION",
        "value": backup_mount_location
    }, {
        "name": "USER_CLAIM_LOCATION",
        "value": user_mount_location
    }, {
        "name": "PRIVATE_SIGNING_KEY",
        "value": "/etc/signing/public/ass_rsa.public"
    }]
    pod_body = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': name_long
        },
        'spec': {
            'containers': [{
                'name': "backup",
                'image': image,
                'env': env,
                'volumeMounts': volume_mounts
            }],
            'volumes': volumes,
            'restartPolicy': 'Never'
        }
    }
    print(core_v1.create_namespaced_pod(namespace='default', body=pod_body))

def read_write_many(claim_name=None, core_v1=None):
    """
    To mount a persistent volume claim to multiple pods, we need it to be
    ReadWriteMany, you can't change the PVC, but you can change the persistent
    volume underlying it. This is what we do here.
    """
    # A patch operation.
    pv_operation = {"op": "replace", "path": "/spec/accessModes/0/", "value": "ReadWriteMany"}
    # Get pvc
    pvc = core_v1.list_namespaced_persistent_volume_claim(namespace='default', field_selector='metadata.name={}'.format(claim_name))
    if len(pvc.items) > 0:
        # Get pv
        pv_name = pvc.items[0].spec.volume_name
        res = core_v1.patch_persistent_volume(name=pv_name, body=pv_operation)

def cleanup_pod(name_long=None, core_v1=None):
    try:
        print(core_v1.delete_namespaced_pod(namespace='default', name=name_long))
    except ApiException:
        pass

def cleanup_job(job_id: str = None, user: str = None, core_v1=None):
    # Job only creates one pod.
    cleanup_pod(name_long="backup-{}-{}".format(job_id, user), core_v1=core_v1)

def backup_job(job_id: str = None, user: str = None, core_v1=None):
    # Step 1. Ensure the claim is ReadWriteMany.
    read_write_many(claim_name="claim-{}".format(user), core_v1=core_v1)
    # Step 2. Launch Job to copy from user jupyter claim to destination.
    launch_backup_job(name_long="backup-{}-{}".format(job_id, user),
                      user=user,
                      job_id=job_id,
                      core_v1=core_v1)


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

def delete_pvc(user=None, core_v1=None):
    print(core_v1.delete_namespaced_persistent_volume_claim(name="claim-{}".format(user), namespace='default'))

def determine_job_type(description: Dict[Any, Any]) -> Optional[str]:
    if "backup" in description.keys():
        return "backup"
    elif "delete" in description.keys():
        return "delete"
    elif "delete_pvc" in description.keys():
        return "remove_pvc"
    else:
        return None

config.load_incluster_config()

core_v1 = core_v1_api.CoreV1Api()

job_id = list(sys.argv)[1]
encrypted_payload = list(sys.argv)[2]

# Decode job.
decoded_payload = decode(encrypted_payload)
# Note: This will fail if the value is not valid JSON.
job_json = json.loads(decoded_payload)

# Check whether job is for backup or completion of the backup.
job_type = determine_job_type(job_json)

if job_type == "delete":
    cleanup_job(job_id=job_json['job_id'], user=job_json['delete'], core_v1=core_v1)
elif job_type == "backup":
    backup_job(job_id=job_id, user=job_json['backup'], core_v1=core_v1)
elif job_type == "remove_pvc":
    delete_pvc(user=job_json['delete_pvc'], core_v1=core_v1)