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

def cleanup_volumes(job_id: str = None, core_v1=None):
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="submission-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="setup-config-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="verify-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="test-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="results-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass
    try:
        print(core_v1.delete_namespaced_persistent_volume_claim(name="finalise-eph-{}".format(job_id), namespace='default'))
    except ApiException:
        pass

def cleanup_pod(name_long=None, core_v1=None):
    try:
        print(core_v1.delete_namespaced_pod(namespace='default', name=name_long))
    except ApiException:
        pass

def cleanup_job(job_id: str = None, core_v1=None):
    cleanup_pod(name_long="submit-finalise-{}".format(job_id), core_v1=core_v1)
    cleanup_pod(name_long="submit-results-{}".format(job_id), core_v1=core_v1)
    cleanup_pod(name_long="submit-test-{}".format(job_id), core_v1=core_v1)
    cleanup_pod(name_long="submit-verify-{}".format(job_id), core_v1=core_v1)
    cleanup_pod(name_long="submit-setup-{}".format(job_id), core_v1=core_v1)
    cleanup_volumes(job_id=job_id, core_v1=core_v1)

config.load_incluster_config()

core_v1 = core_v1_api.CoreV1Api()

print(list(sys.argv))

job_id = list(sys.argv)[1]

cleanup_job(job_id=job_id, core_v1=core_v1)
