#!/usr/bin/env python

import time
import os
import rediswq

host = os.getenv("REDIS_SERVICE_NAME", "redis")
# Uncomment next two lines if you do not have Kube-DNS working.
# import os
# host = os.getenv("REDIS_SERVICE_HOST")

q = rediswq.RedisWQ(name=os.getenv("SUBMIT_QUEUE_NAME", default="submit"), host=host)
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))
while True:
  item = q.lease(lease_secs=10, block=True, timeout=2)
  if item is not None:
    itemstr = item.decode("utf-8")
    print("Working on " + itemstr)
    time.sleep(10) # Put your actual work here instead of sleep.
    # TODO GJF: Instead of sleep, generate a random string and generate a job to
    #   handle the item on the queue if it fits the required form.
    q.complete(item)
  else:
    print("Waiting for work")
  while q.empty():
    # Sleep while we wait for work.
    time.sleep(30)
print("Queue empty, exiting")
