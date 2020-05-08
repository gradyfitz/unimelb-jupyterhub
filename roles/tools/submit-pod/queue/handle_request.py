"""
Borrows heavily from examples in
https://github.com/kubernetes-client/python/tree/master/examples
"""
import time
import sys, os

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
#from kubernetes.

def get_volume_body(name: str = None, storage: str = None):
    body = {
        'apiVersion': 'v1',
        'kind': 'PersistentVolumeClaim',
        'metadata': {
            'name': name
        },
        'spec': {
            'storageClassName': 'csi-cephfs',
            'accessModes': ['ReadWriteMany'],
            'resources': {
                'requests': {
                    'storage': storage
                }
            },
            'volumeMode': 'Filesystem'
        }
    }
    return body

def create_volumes(job_id: str = None, core_v1=None):

    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="submission-eph-{}".format(job_id), storage="64Mi")))
    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="setup-config-eph-{}".format(job_id), storage="64Mi")))
    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="verify-eph-{}".format(job_id), storage="128Mi")))
    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="test-eph-{}".format(job_id), storage="128Mi")))
    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="results-eph-{}".format(job_id), storage="128Mi")))
    print(core_v1.create_namespaced_persistent_volume_claim(namespace='default', body=get_volume_body(name="finalise-eph-{}".format(job_id), storage="128Mi")))

def create_pod(name_short=None, name_long=None, image=None, env=None, volume_mounts=None, volumes=None, core_v1=None):
    pod_body = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': name_long
        },
        'spec': {
            'containers': [{
                'name': name_short,
                'image': image,
                'env': env,
                'volumeMounts': volume_mounts
            }],
            'volumes': volumes,
            'restartPolicy': 'Never'
        }
    }
    print(core_v1.create_namespaced_pod(namespace='default', body=pod_body))

def get_setup_env(job_id: str = None, submitted_filename: str = None, file_sig: str = None, assignment: str = None, username: str = None):

    SETUP_ENVS = [
    {"name": "JOB_ID", "value": job_id},
    {"name": "ASSIGNMENT_NAME", "value": assignment},
    {"name": "RAW_SUBMISSIONS_FOLDER", "value": "/home/raw_submissions"},
    {"name": "SUBMISSION_FOLDER", "value": "/home/student_mount"},
    {"name": "SUBMISSION_EPH_FOLDER", "value": "/home/submission_eph"},
    {"name": "USERNAME", "value": username},
    {"name": "ASSIGNMENT_SETUP_FOLDER", "value": "/home/assignment_config"},
    {"name": "SETUP_META_DATA_FOLDER", "value": "/home/setup_config_eph"},
    {"name": "SETUP_META_DATA_NAME", "value": "setup.log"},
    {"name": "SETUP_CONFIG_FILE_NAME", "value": "setup.txt"},
    {"name": "SETUP_RESULT_FILE", "value": "__setup_result.txt"},
    {"name": "VERIFICATION_DATA_FOLDER", "value": "/home/verify_eph"},
    {"name": "TESTING_DATA_FOLDER", "value": "/home/test_eph"},
    {"name": "RESULTS_DATA_FOLDER", "value": "/home/results_eph"},
    {"name": "FINALISE_DATA_FOLDER", "value": "/home/finalise_eph"},
    {"name": "STUDENT_PRIVATE_OUTPUT_FOLDER", "value": "/home/private_output"},
    {"name": "SUBMITTED_FILENAME", "value": submitted_filename},
    {"name": "FILE_SIGNATURE", "value": file_sig},
    {"name": "PRIVATE_SIGNING_KEY", "value": "/etc/signing/private/ass_rsa.private"}
    ]
    return SETUP_ENVS

def get_verify_env(job_id: str = None, submitted_filename: str = None, file_sig: str = None, assignment: str = None, username: str = None):
    VERIFY_ENVS = [
    {"name": "JOB_ID", "value": job_id},
    {"name": "ASSIGNMENT_NAME", "value": assignment},
    {"name": "SUBMISSION_FOLDER", "value": "/home/submission_eph"},
    {"name": "USERNAME", "value": username},
    {"name": "SETUP_META_DATA_FOLDER", "value": "/home/setup_config_eph"},
    {"name": "VERIFICATION_OUTPUT_FOLDER", "value": "/home/verify_eph"},
    {"name": "SETUP_RESULT_FILE", "value": "__setup_result.txt"},
    {"name": "VERIFICATION_DATA_FOLDER", "value": "/home/verify_eph"},
    {"name": "VERIFICATION_DATA_OUTPUT_NAME", "value": "__verify_result.txt"},
    {"name": "SUBMITTED_FILENAME", "value": submitted_filename},
    {"name": "FILE_SIGNATURE", "value": file_sig}
    ]
    return VERIFY_ENVS

def get_test_env(job_id: str = None, submitted_filename: str = None, file_sig: str = None, assignment: str = None, username: str = None):
    TEST_ENVS = [
    {"name": "JOB_ID", "value": job_id},
    {"name": "ASSIGNMENT_NAME", "value": assignment},
    {"name": "SUBMISSION_FOLDER", "value": "/home/submission_eph"},
    {"name": "USERNAME", "value": username},
    {"name": "VERIFICATION_OUTPUT_FOLDER", "value": "/home/verify_eph"},
    {"name": "TESTING_OUTPUT_FOLDER", "value": "/home/test_eph"},
    {"name": "VERIFICATION_DATA_FOLDER", "value": "/home/verify_eph"},
    {"name": "VERIFICATION_DATA_OUTPUT_NAME", "value": "__verify_result.txt"},
    {"name": "TESTING_DATA_FOLDER", "value": "/home/test_eph"},
    {"name": "TESTING_DATA_OUTPUT_NAME", "value": "__test_result.txt"},
    {"name": "SUBMITTED_FILENAME", "value": submitted_filename},
    {"name": "FILE_SIGNATURE", "value": file_sig}
    ]
    return TEST_ENVS

def get_results_env(job_id: str = None, submitted_filename: str = None, file_sig: str = None, assignment: str = None, username: str = None):
    RESULTS_ENVS = [
    {"name": "JOB_ID", "value": job_id},
    {"name": "ASSIGNMENT_NAME", "value": assignment},
    {"name": "STUDENT_OUTPUT_FOLDER", "value": "/home/student_mount"},
    {"name": "SUBMISSION_FOLDER", "value": "/home/submission_eph"},
    {"name": "USERNAME", "value": username},
    {"name": "SETUP_META_DATA_FOLDER", "value": "/home/setup_config_eph"},
    {"name": "VERIFICATION_OUTPUT_FOLDER", "value": "/home/verify_eph"},
    {"name": "TESTING_OUTPUT_FOLDER", "value": "/home/test_eph"},
    {"name": "SETUP_META_DATA_NAME", "value": "setup.log"},
    {"name": "SETUP_CONFIG_FILE_NAME", "value": "setup.txt"},
    {"name": "SETUP_RESULT_FILE", "value": "__setup_result.txt"},
    {"name": "VERIFICATION_DATA_FOLDER", "value": "/home/verify_eph"},
    {"name": "VERIFICATION_DATA_OUTPUT_NAME", "value": "__verify_result.txt"},
    {"name": "TESTING_DATA_FOLDER", "value": "/home/test_eph"},
    {"name": "TESTING_DATA_OUTPUT_NAME", "value": "__test_result.txt"},
    {"name": "RESULTS_DATA_FOLDER", "value": "/home/results_eph"},
    {"name": "RESULTS_DATA_OUTPUT_NAME", "value": "__results_result.txt"},
    {"name": "RESULTS_OUTPUT_FOLDER", "value": "/home/results_eph"},
    {"name": "STUDENT_PRIVATE_OUTPUT_FOLDER", "value": "/home/private_output"},
    {"name": "SUBMITTED_FILENAME", "value": submitted_filename},
    {"name": "FILE_SIGNATURE", "value": file_sig}
    ]
    return RESULTS_ENVS

def get_finalise_env(job_id: str = None, submitted_filename: str = None, file_sig: str = None, assignment: str = None, username: str = None):
    FINALISE_ENVS = [
    {"name": "JOB_ID", "value": job_id},
    {"name": "ASSIGNMENT_NAME", "value": assignment},
    {"name": "STUDENT_OUTPUT_FOLDER", "value": "/home/student_mount"},
    {"name": "SUBMISSION_FOLDER", "value": "/home/submission_eph"},
    {"name": "USERNAME", "value": username},
    {"name": "ASSIGNMENT_SETUP_FOLDER", "value": "/home/assignment_config"},
    {"name": "SETUP_META_DATA_FOLDER", "value": "/home/setup_config_eph"},
    {"name": "VERIFICATION_OUTPUT_FOLDER", "value": "/home/verify_eph"},
    {"name": "TESTING_OUTPUT_FOLDER", "value": "/home/test_eph"},
    {"name": "SETUP_META_DATA_NAME", "value": "setup.log"},
    {"name": "SETUP_CONFIG_FILE_NAME", "value": "setup.txt"},
    {"name": "SETUP_RESULT_FILE", "value": "__setup_result.txt"},
    {"name": "VERIFICATION_DATA_FOLDER", "value": "/home/verify_eph"},
    {"name": "VERIFICATION_DATA_OUTPUT_NAME", "value": "__verify_result.txt"},
    {"name": "TESTING_DATA_FOLDER", "value": "/home/test_eph"},
    {"name": "TESTING_DATA_OUTPUT_NAME", "value": "__test_result.txt"},
    {"name": "RESULTS_DATA_FOLDER", "value": "/home/results_eph"},
    {"name": "RESULTS_DATA_OUTPUT_NAME", "value": "__results_result.txt"},
    {"name": "RESULTS_OUTPUT_FOLDER", "value": "/home/results_eph"},
    {"name": "FINALISE_META_OUTPUT_FILE", "value": "/home/finalise_eph/__finalise.log"},
    {"name": "FINALISE_META_OUTPUT_FILE_TEMP", "value": "/home/finalise_eph/__finalise_temp.log"},
    {"name": "FINALISE_DATA_FOLDER", "value": "/home/finalise_eph"},
    {"name": "STUDENT_PRIVATE_OUTPUT_FOLDER", "value": "/home/private_output"},
    {"name": "SUBMITTED_FILENAME", "value": submitted_filename},
    {"name": "FILE_SIGNATURE", "value": file_sig}
    ]
    return FINALISE_ENVS

SETUP_VM = [
{"name": "raw-submissions", "mountPath": "/home/raw_submissions"},
{"name": "student-claim", "mountPath": "/home/student_mount"},
{"name": "submission-eph", "mountPath": "/home/submission_eph"},
{"name": "assignment-config", "mountPath": "/home/assignment_config"},
{"name": "setup-config-eph", "mountPath": "/home/setup_config_eph"},
{"name": "verify-eph", "mountPath": "/home/verify_eph"},
{"name": "test-eph", "mountPath": "/home/test_eph"},
{"name": "results-eph", "mountPath": "/home/results_eph"},
{"name": "finalise-eph", "mountPath": "/home/finalise_eph"},
{"name": "private-results", "mountPath": "/home/private_output"},
{"name": "private-rsa-key", "mountPath": "/etc/signing/private"},
{"name": "public-rsa-key", "mountPath": "/etc/signing/public"}
]

VERIFY_VM = [
{"name": "submission-eph", "mountPath": "/home/submission_eph"},
{"name": "setup-config-eph", "mountPath": "/home/setup_config_eph"},
{"name": "verify-eph", "mountPath": "/home/verify_eph"}
]

TEST_VM = [
{"name": "submission-eph", "mountPath": "/home/submission_eph"},
{"name": "verify-eph", "mountPath": "/home/verify_eph"},
{"name": "test-eph", "mountPath": "/home/test_eph"}
]

RESULTS_VM = [
{"name": "student-claim", "mountPath": "/home/student_mount"},
{"name": "submission-eph", "mountPath": "/home/submission_eph"},
{"name": "setup-config-eph", "mountPath": "/home/setup_config_eph"},
{"name": "verify-eph", "mountPath": "/home/verify_eph"},
{"name": "test-eph", "mountPath": "/home/test_eph"},
{"name": "results-eph", "mountPath": "/home/results_eph"},
{"name": "private-results", "mountPath": "/home/private_output"}
]

FINALISE_VM = [
{"name": "student-claim", "mountPath": "/home/student_mount"},
{"name": "submission-eph", "mountPath": "/home/submission_eph"},
{"name": "assignment-config", "mountPath": "/home/assignment_config"},
{"name": "setup-config-eph", "mountPath": "/home/setup_config_eph"},
{"name": "verify-eph", "mountPath": "/home/verify_eph"},
{"name": "test-eph", "mountPath": "/home/test_eph"},
{"name": "results-eph", "mountPath": "/home/results_eph"},
{"name": "finalise-eph", "mountPath": "/home/finalise_eph"},
{"name": "private-results", "mountPath": "/home/private_output"}
]

def get_setup_volumes(job_id: str = None, username: str = None):
    SETUP_VOLUMES = [
    {"name": "student-claim",
    "persistentVolumeClaim": {
    "claimName": "claim-{}".format(username)}},
    {"name": "raw-submissions",
    "persistentVolumeClaim": {
    "claimName": "submit-raw-submissions"}},
    {"name": "assignment-config",
    "persistentVolumeClaim": {
    "claimName": "submit-assignment-config"}},
    {"name": "submission-eph",
    "persistentVolumeClaim": {
    "claimName": "submission-eph-{}".format(job_id)}},
    {"name": "setup-config-eph",
    "persistentVolumeClaim": {
    "claimName": "setup-config-eph-{}".format(job_id)}},
    {"name": "verify-eph",
    "persistentVolumeClaim": {
    "claimName": "verify-eph-{}".format(job_id)}},
    {"name": "test-eph",
    "persistentVolumeClaim": {
    "claimName": "test-eph-{}".format(job_id)}},
    {"name": "results-eph",
    "persistentVolumeClaim": {
    "claimName": "results-eph-{}".format(job_id)}},
    {"name": "finalise-eph",
    "persistentVolumeClaim": {
    "claimName": "finalise-eph-{}".format(job_id)}},
    {"name": "private-results",
    "persistentVolumeClaim": {
    "claimName": "submit-private-results"}},
    {"name": "private-rsa-key",
    "secret": {
    "secretName": "ass-rsa-private"}},
    {"name": "public-rsa-key",
    "secret": {
    "secretName": "ass-rsa-public"}}
    ]
    return SETUP_VOLUMES

def get_verify_volumes(job_id: str = None, username: str = None):
    VERIFY_VOLUMES = [
 {"name": "submission-eph",
  "persistentVolumeClaim": {
    "claimName": "submission-eph-{}".format(job_id)}},
 {"name": "setup-config-eph",
  "persistentVolumeClaim": {
    "claimName": "setup-config-eph-{}".format(job_id)}},
 {"name": "verify-eph",
  "persistentVolumeClaim": {
    "claimName": "verify-eph-{}".format(job_id)}}
    ]
    return VERIFY_VOLUMES

def get_test_volumes(job_id: str = None, username: str = None):
    TEST_VOLUMES = [
    {"name": "submission-eph",
  "persistentVolumeClaim":
    {"claimName": "submission-eph-{}".format(job_id)}},
{"name": "verify-eph",
  "persistentVolumeClaim":
    {"claimName": "verify-eph-{}".format(job_id)}},
{"name": "test-eph",
  "persistentVolumeClaim":
    {"claimName": "test-eph-{}".format(job_id)}}
    ]
    return TEST_VOLUMES

def get_results_volumes(job_id: str = None, username: str = None):
    RESULTS_VOLUMES = [
    {"name": "student-claim",
  "persistentVolumeClaim":
    {"claimName": "claim-{}".format(username)}},
{"name": "submission-eph",
  "persistentVolumeClaim":
    {"claimName": "submission-eph-{}".format(job_id)}},
{"name": "setup-config-eph",
  "persistentVolumeClaim":
    {"claimName": "setup-config-eph-{}".format(job_id)}},
{"name": "verify-eph",
  "persistentVolumeClaim":
    {"claimName": "verify-eph-{}".format(job_id)}},
{"name": "test-eph",
  "persistentVolumeClaim":
    {"claimName": "test-eph-{}".format(job_id)}},
{"name": "results-eph",
  "persistentVolumeClaim":
    {"claimName": "results-eph-{}".format(job_id)}},
{"name": "private-results",
  "persistentVolumeClaim":
    {"claimName": "submit-private-results"}}
    ]
    return RESULTS_VOLUMES

def get_finalise_volumes(job_id: str = None, username: str = None):
    FINALISE_VOLUMES = [
    {"name": "student-claim",
  "persistentVolumeClaim":
    {"claimName": "claim-{}".format(username)}},
{"name": "assignment-config",
  "persistentVolumeClaim":
    {"claimName": "submit-assignment-config"}},
{"name": "submission-eph",
  "persistentVolumeClaim":
    {"claimName": "submission-eph-{}".format(job_id)}},
{"name": "setup-config-eph",
  "persistentVolumeClaim":
    {"claimName": "setup-config-eph-{}".format(job_id)}},
{"name": "verify-eph",
  "persistentVolumeClaim":
    {"claimName": "verify-eph-{}".format(job_id)}},
{"name": "test-eph",
  "persistentVolumeClaim":
    {"claimName": "test-eph-{}".format(job_id)}},
{"name": "results-eph",
  "persistentVolumeClaim":
    {"claimName": "results-eph-{}".format(job_id)}},
{"name": "finalise-eph",
  "persistentVolumeClaim":
    {"claimName": "finalise-eph-{}".format(job_id)}},
{"name": "private-results",
  "persistentVolumeClaim":
    {"claimName": "submit-private-results"}}
    ]
    return FINALISE_VOLUMES

def create_job(job_id: str = None, submit_mode: str = None, username: str = None, assignment: str = None, zip_hash: str = None, submit_path: str = None, core_v1=None):

    create_volumes(job_id=job_id, core_v1=core_v1)
    create_pod(name_short="submit-setup", name_long="submit-setup-{}".format(job_id), image="gradyfitz/submit-setup", env=get_setup_env(job_id=job_id, submitted_filename=submit_path, file_sig=zip_hash, assignment=assignment, username=username), volume_mounts=SETUP_VM, volumes=get_setup_volumes(job_id=job_id, username=username), core_v1=core_v1)
    create_pod(name_short="submit-verify", name_long="submit-verify-{}".format(job_id), image="gradyfitz/submit-verify", env=get_verify_env(job_id=job_id, submitted_filename=submit_path, file_sig=zip_hash, assignment=assignment, username=username), volume_mounts=VERIFY_VM, volumes=get_verify_volumes(job_id=job_id, username=username), core_v1=core_v1)
    create_pod(name_short="submit-test", name_long="submit-test-{}".format(job_id), image="gradyfitz/submit-test", env=get_test_env(job_id=job_id, submitted_filename=submit_path, file_sig=zip_hash, assignment=assignment, username=username), volume_mounts=TEST_VM, volumes=get_test_volumes(job_id=job_id, username=username), core_v1=core_v1)
    create_pod(name_short="submit-results", name_long="submit-results-{}".format(job_id), image="gradyfitz/submit-results", env=get_results_env(job_id=job_id, submitted_filename=submit_path, file_sig=zip_hash, assignment=assignment, username=username), volume_mounts=RESULTS_VM, volumes=get_results_volumes(job_id=job_id, username=username), core_v1=core_v1)
    create_pod(name_short="submit-finalise", name_long="submit-finalise-{}".format(job_id), image="gradyfitz/submit-finalise", env=get_finalise_env(job_id=job_id, submitted_filename=submit_path, file_sig=zip_hash, assignment=assignment, username=username), volume_mounts=FINALISE_VM, volumes=get_finalise_volumes(job_id=job_id, username=username), core_v1=core_v1)

def pvc_exists(claim: str = None, core_v1 = None):
    res = core_v1.list_namespaced_persistent_volume_claim(namespace='default', field_selector='metadata.name={}'.format(claim))
    if len(res.items) > 0:
        return True
    else:
        return False


config.load_incluster_config()

core_v1 = core_v1_api.CoreV1Api()

print(list(sys.argv))

# Note that jobs are also incremented for cleanup.
job_id = list(sys.argv)[1]

#command_type = list(sys.argv)[2]

# submit_mode, username, assignment, zip_hash, submit_path
if len(list(sys.argv)) < 5:
    print("Incorrect number of arguments to command ({}).".format(len(sys.argv)))
    exit(1)

submit_mode = list(sys.argv)[2]
username = list(sys.argv)[3]
assignment = list(sys.argv)[4]
zip_hash = list(sys.argv)[5]
submit_path = " ".join(list(sys.argv)[6:])

if not submit_mode == "submit":
    print("Unhandled submission mode {}.".format(submit_mode))
    exit(1)

# Check the assignment exists.
assignment_exists = os.popen('/bin/bash -c "if [[ -d {}/{} ]]; then printf True; else printf False; fi"'.format(os.getenv("ASSIGNMENT_CONFIG_FOLDER"), assignment)).read()
if assignment_exists == "False":
    print("Assignment {} not found.".format(assignment))
    exit(1)

# Check the student claim exists.
if not pvc_exists(claim="claim-{}".format(username), core_v1=core_v1):
    print("User {}'s claim not found, ignoring submission.".format(username))
    exit(1)

create_job(job_id=job_id, submit_mode=submit_mode, username=username, assignment=assignment, zip_hash=zip_hash, submit_path=submit_path, core_v1=core_v1)
