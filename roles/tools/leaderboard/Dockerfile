FROM python

ARG REDIS_SERVICE_NAME="redis"
ARG SUBMIT_QUEUE_NAME="leaderboard"

ENV REDIS_SERVICE_NAME=$REDIS_SERVICE_NAME
ENV SUBMIT_QUEUE_NAME=$SUBMIT_QUEUE_NAME

RUN pip install redis kubernetes
COPY ./worker.py /worker.py
COPY ./rediswq.py /rediswq.py
COPY ./handle_request.py /handle_request.py
COPY ./handle_update.py /handle_update.py

RUN pip install pycryptodome sympy pandas 

CMD  /bin/bash -c "(python handle_update.py &); python worker.py"
USER root