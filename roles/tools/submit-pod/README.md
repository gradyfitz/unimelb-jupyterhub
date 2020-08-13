# Submit System for JupyterHub

Adapted from:
https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/

This submit system is intended to handle simple assignment submission,
processing plagiarism analysis and leaderboard update as well as authentication.

## How it Works
The system uses the simple Redis queue set up above and uses the pipe submit to
launch jobs which process the provided submission.

## How to set up
1. Copy the queue/redis-pod.yaml, queue/redis-service.yaml,
  queue/ingest-job.yaml and reaper/reaper-job.yaml files to the server.
2. Run `kubectl create -f redis-pod.yaml`
3. Run `kubectl create -f redis-service.yaml`
4. Run `kubectl create -f ingest-job.yaml`
5. Run `kubectl create -f reaper-job.yaml`
6. If it hasn't been applied before, apply the permissions in
  roles/tools/permissions/README.md

## Default Setup Scheme
The way I've aimed to set up the system is simple.
1. The user prepares the files into a single zip archive then stores this in
  their /home/jovyan/submissions directory.
2. The user then creates an empty file with the same basename as the zip
  archive and a .txt extension.
3. The user connects to the redis service and gives it a string matching the
  form:

  - user assignment checksum filepath

  where the user is the student's username, checksum is the checksum of the file
  at the given filepath and filepath is the location on the disk with the file.

  Note that this filepath must contain no spaces, contain only alphanumeric,
  slashes ('/') or dashes ('-'). All other content will be dropped silently as
  garbage. The checksum will be a SHA1 file hash.
4. All the subsequent processes will write to the text document created in step
  2 which can be checked at any time by the user.
5. Add keys to each admin user's account.

## Order of Events
1. A worker node pod pulls the next item from the redis queue.
2. The worker node evaluates the request is within the required size and that
  checksum match.
3. The worker node launches a lightweight verify step job. This copies the file
  to a pod controlled volume and is eventually written to the private redis
  queue for the given user if this verify step passes. At this point the file
  created by the user is updated with the details that it passed or failed the
  verify step. The student should already know what the result of this is by
  running locally, but we reperform this step to ensure the local environment
  the student tests in matches the one we use for full testing.
4. Two pods are created, one to run tests and generate the results to be
  output and one to process these, sharing a private results volume.
5. The data is also copied to a second volume which is ephemeral for the test
  itself (in case the act of testing damages the original files).
6. The processing pod waits for a ready file, once this is created processing
  begins on the results returned.
7. The post-processing pod processes the results and then pushes to the private
  redis for the leaderboard update step.
8. The files are set up for MOSS processing.
9. An admin

## Pipe Structure
For submission, seven queues are utilised:
1. The "submit" queue, this is intended to be accessible by students and holds
  the `user assignment checksum filepath` content submitted by the student.
2. The "prepared" queue, this is given for the particular job, a message
  is sent to this queue when the assignment has been copied for the volume for
  verification.
3. The "process" queue, this is given for the particular job, a message is
  sent to this queue when the verification step for the job is done.
4. The "test" queue, this is given for the particular job, a message is sent to
  this queue when the testing step for the job is done.
5. The "finished" queue, this is given for the particular job, a message is sent
  to this queue when the results processing step for the job is done.
6. The "result" queue, this is given for the particular job, a message is sent
  to this queue when all consequences for the results have been applied.
7. The "user" queue, this is given across all jobs for a user, it logs the
  status of the job. No information beyond the submit information about the job
  is exposed except for the timings of completion and the pass/fail result of
  verification.
