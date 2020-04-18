ARG REPO_TAG="user"
FROM gradyfitz/comp20003-jupyter-c-kernel:$REPO_TAG

ENV REDIS_WAIT_SCRIPT_LOCATION="/home/utils/wait.sh"
ENV REDIS_NOTIFICATION_SCRIPT_LOCATION="/home/utils/notification.sh"

COPY ./wait_queue.py $REDIS_WAIT_SCRIPT_LOCATION
COPY ./notify_queue.py $REDIS_NOTIFICATION_SCRIPT_LOCATION
