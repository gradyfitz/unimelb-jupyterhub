#!/usr/bin/env python

import time
import os, sys
import rediswq

host = os.getenv("REDIS_SERVICE_NAME", "redis")
# Uncomment next two lines if you do not have Kube-DNS working.
# import os
# host = os.getenv("REDIS_SERVICE_HOST")
job_number = int(os.getenv("INITIAL_JOB_NUMBER", "1"))

q = rediswq.RedisWQ(name=os.getenv("SUBMIT_QUEUE_NAME", default="submit"), host=host)
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))
while True:
  # Sleep for 45 seconds between all submissions to give kubernetes time to spin up
  # containers when required.
  item = q.lease(lease_secs=300, block=True, timeout=2)
  if item is not None:
    itemstr = item.decode("utf-8")
    print("Working on " + itemstr)
    time.sleep(int(os.getenv("LAUNCH_DELAY", "10"))) # Put your actual work here instead of sleep.
    print(os.popen('python /handle_request.py {:05d} {} > last_job.txt'.format(job_number, itemstr)).read(), file=sys.stderr)
    job_number = job_number + 1
    q.complete(item)
    time.sleep(int(os.getenv("AFTER_JOB_WAIT", "45")))
  else:
    print("Waiting for work")
  while q.empty():
    # Sleep while we wait for work.
    time.sleep(int(os.getenv("IDLE_WAIT", "30")))
print("Queue empty, exiting")
