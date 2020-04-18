FROM python

ARG REDIS_SERVICE_NAME="redis"
ARG SUBMIT_QUEUE_NAME="submit"

ENV REDIS_SERVICE_NAME=$REDIS_SERVICE_NAME
ENV SUBMIT_QUEUE_NAME=$SUBMIT_QUEUE_NAME

RUN pip install redis kubernetes
COPY ./worker.py /worker.py
COPY ./rediswq.py /rediswq.py

CMD  python worker.py
