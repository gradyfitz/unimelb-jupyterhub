from gradyfitz/comp20003-jupyter-c-kernel:admin

# Root just in case.
USER root
ENV REDIS_WAIT_SCRIPT_LOCATION="/home/utils/wait.py"
ENV REDIS_NOTIFICATION_SCRIPT_LOCATION="/home/utils/notification.py"

RUN pip install pycryptodome

COPY ./wait_queue.py $REDIS_WAIT_SCRIPT_LOCATION
COPY ./notify_queue.py $REDIS_NOTIFICATION_SCRIPT_LOCATION
COPY ./submitutils.py /home/utils/submitutils.py
COPY ./markutils.py /home/utils/markutils.py
COPY ./backup.py /home/utils/backup.py

CMD ["/bin/bash", "-c", "cd /home/utils && python backup.py"]