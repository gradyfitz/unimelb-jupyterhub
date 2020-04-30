"""
This script waits until a message enters the queue given as an argument and then consumes that value.
"""

import os, sys
import time
import redis

def wait_for_queue(queue: str) -> None:
    """
        Continues trying to remove an item from
        the given queue until it is able to do so
        successfully, then returns.
    """
    r = redis.Redis(host="redis")
    
    while True:
        item = r.lpop(queue)
        if item is None:
            # Sleep for ten seconds.
            time.sleep(10)
        else:
            return

wait_for_queue(queue=(" ".join(sys.argv[1:])))
