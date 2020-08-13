# Adding Isolated Run and Test Server
One example provided is a ingest, verify, test and report system. This system
employs a number of techniques to ensure students are given maximal ability to
run arbitrary code with as little file-system and environmental risk as
possible. This is performed at a few levels and this document aims to explain
the system.

1. Prerequisites
2. Submission Security
3. Message Passing Protocol
4. Volumes
5. Volume Permissions
6. Extensions
7. Building the Containers
8. Scalability
9. Setup and Deployment

## Prerequisites
The system pulls the submission from the submitting user's persistent volume
claim. This means all persistent volumes must be ReadWriteMany, or else the
submission may be jammed until the user logs off long enough that their server
becomes inactive.

## Submission Security
The permissions model is quite simple, we assume that students are the only ones
with control over their persistent volume claim, being able to submit a
submission successfully with a correct checksum is considered proof that the
student themselves made this request.

## Message Passing Protocol
The system makes heavy use of message passing to operate. This process is as
follows.

1. A user sends a request to the queue server to ingest a solution from their
  local directory.
2. The queue server reads this message and then allocates the job a unique ID
  and passes it on to the setup queue for that job and launches the system for
  that ID.
3. The setup pod sets up the environment for the following steps and then sends
  a message to the verify pod for the job ID.
4. The verify pod verifies the result and then passes the result of the
  verification to the test pod for the job ID.
5. The test pod then tests the submission and notifies the results pod that the
  testing is complete for the job ID.
6. The results pod then investigates the output of the test pod and once all
  results processing is complete, it hands over to the finalise pod.
7. The finalise pod completes any final cleanup steps and then sends a message
  to the reaper that the job is complete.
8. Upon receiving the notification, the reaper deletes all pods in the job.

## Volumes
The system uses a number of volumes which are attached at different stages of
the process to be used in a number of different ways.

1. Student Claim - The JupyterHub volume the student uses, their solution will
  be stored somewhere here initially.
2. Assignment Configuration Volume - A source for initial assignment scripts.
3. Raw Submissions Volume - Snapshots of all solutions which fit required size
  limits are added here (this takes the ability to make changes after
  submission away from students).
4. Private Results Volume - A location to store all results that tutors will
  see, e.g. those results with hidden tests or additional output not shown to
  students.
5. Ephemeral Setup Configuration Volume - Contains setup scripts to be used
  during test process.
6. Ephemeral Submission Volume - Contains submission scripts to be used during
  test process.
7. Ephemeral Verification Volume - Contains verification scripts to be used during
  test process.
8. Ephemeral Testing Volume - Contains testing scripts to be used during test
  process.
9. Ephemeral Results Volume - Contains results scripts to be used during test
  process.
10. Ephemeral Finalisation Volume - Contains finalisation scripts to be used
  during test process.

Volumes 5 - 10 are deleted after the conclusion of the job.

## Volume Permissions
Different volumes are visible at different stages to reflect a difference in
trust levels. We consider all volumes visible in the Verify and Test stages to
be inherently and fully under student control, but all volumes only visible at
Setup, Results and/or Finalise stages to be fully safe from student
interference.

1. The Setup pod sees the volumes:
  - Student Claim
  - Assignment Configuration Volume
  - Raw Submissions Volume
  - Ephemeral Setup Configuration Volume
  - Ephemeral Submission Volume

2. The Verify pod sees the volumes:
  - Ephemeral Setup Configuration Volume
  - Ephemeral Submission Volume
  - Ephemeral Verification Volume

3. The Test pod sees the volumes:
  - Ephemeral Submission Volume
  - Ephemeral Verification Volume
  - Ephemeral Testing Volume

4. The Results pod sees the volumes:
  - Student Claim
  - Private Results Volume
  - Ephemeral Setup Configuration Volume
  - Ephemeral Submission Volume
  - Ephemeral Verification Volume
  - Ephemeral Testing Volume
  - Ephemeral Results Volume

5. The Finalise pod sees the volumes:
  - Student Claim
  - Assignment Configuration Volume
  - Private Results Volume
  - Ephemeral Setup Configuration Volume
  - Ephemeral Submission Volume
  - Ephemeral Verification Volume
  - Ephemeral Testing Volume
  - Ephemeral Results Volume
  - Ephemeral Finalisation Volume

6. JupyterHub Admins are intended to see the volumes:
  - Assignment Configuration Volume
  - Raw Submissions Volume
  - Private Results Volume

## Extensions
The finalise scripts allow a large variety of options through additional
  messages, leading into ideas such as the reaper pod and a leaderboard system
  (see doc/05_leaderboard.md).

## Building the Containers
If you want to make changes to the base image or deploy locally, the submission
system containers might need to be built. Build them by the following process.

1. Build the shared image, tag it and push it. The example images push this to
  gradyfitz/submit-shared, so if you want to push to somewhere else, make that
  change in all the Dockerfiles in roles/tools/submit-pod/\*/Dockerfile
2. Build the image in roles/tools/submit-pod/queue, if you push to somewhere
  different than gradyfitz/submit-generic-schedule, change the values in
  ingest-job.yaml
3. Build all the other images in roles/tools/submit-pod/\*/Dockerfile with the
  folder as build environment.

These builds are critical to ensure the testing environment mirrors the
development environment as closely as possible.

## Scalability
As part of ensuring scalability, it is worthwhile to give enough time that a
full job can be allocated locations on the Kubernetes system before the next job
is allocated. I believe space for more containers should help with this, but I
can't be sure. A cooldown between each launch is more than reasonable.

## Setup and Deployment
Once the images are pushed, there are three steps to get the system up and
running.

1. Add the kubernetes components in roles/tools/submit-pod/kubernetes and
2. Add the secrets matching the examples in roles/tools/submit-pod/secrets/, the
  shell command to create the secrets is given in secret-command.sh, and the
  public key is also given though the private key is missing from this
  repository for obvious reasons.
3. From roles/tools/submit-pod/queue, launch redis-service.yaml, redis-pod.yaml,
  and ingest-job.yaml

