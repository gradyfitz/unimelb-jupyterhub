# Writing Tools for the Kubernetes API
## Queue Pattern
A common pattern useful for performing tasks on Kubernetes is a three step
process.
1. Receive commands in queue.
2. Interact with queue channel in additional container, each command begins a
  new collection of resources to handle the request.
3. The resources complete the request and then mark the work as completed.
4. An additional container processes these completed requests, deleting the
  associated resources.

The operation of this system assumes the existence of a queue, typically redis.
The kubernetes example, The Fine Parallel Processing Work Queue (
https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/ )
is a good place to start. But examples of these tools can be found in
roles/tools (the submit-pod also has its own documentation at doc/04_submit.md):

 - roles/tools/archive - A tool used to backup and archive users.
    - This highlights editing existing resources, encryption & decryption.
 - roles/tools/submit-pod/queue - A tool used to run student submissions
    - This highlights creating pods, volumes and attaching them together.
 - roles/tools/submit-pod/reaper - A tool used to reclaim completed job sets
    once they complete.
    - Highlights delete requests to the kubernetes API.

The python API commands can be found at
https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md

### Notes
To perform operations on kubernetes volumes, the standard jupyterhub role is not
quite enough.

### Roles and Cluster Roles
For a quick run through, for security reasons, users can't directly interact
with kubernetes, anything interacting directly needs a service account. These
service accounts are given varying permissions allowing them to perform
different actions.

Each role can be of two types, a normal Role or a Cluster Role. Normal Roles are
given a namespace to work with and can interact with the cluster in that
namespace in the ways defined by the role with the objects specified. Cluster
Roles on the other hand interact with non-namespaced resources, such as
Persistent Volumes.

### Creating Cluster Roles
Following the instructions in roles/tools/permissions/README.md will add the
permissions.

## General Interaction with Kubernetes
Beyond the JupyterHub extensions, it is possible to interact with the kubernetes
API by creating resources from yaml definitions. Though these abound as the
typical way to interact with Kubernetes when setting up the cluster, a couple
of additional examples are:

  - roles/tools/webserv
    This example shows how to apply a ConfigMap to the system.
  - roles/tools/gitfix_job.yml
    This example shows running a job with a connected student claim.
