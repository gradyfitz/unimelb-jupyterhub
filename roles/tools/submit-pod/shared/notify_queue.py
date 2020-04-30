"""
This script waits until a message enters the queue given as an argument and then consumes that value.
"""

import os, sys
import redis

def push_to_queue(queue: str, value: str) -> None:
    """
        Connects to redis server and pushes content
        value to given queue.
    """
    r = redis.Redis(host="redis")
    r.rpush(queue, value)

push_to_queue(queue=sys.argv[1], value=(" ".join(sys.argv[2:])))
