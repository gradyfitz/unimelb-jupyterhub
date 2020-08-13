FROM python

ARG REDIS_SERVICE_NAME="redis"
ARG SUBMIT_QUEUE_NAME="archive"

ENV REDIS_SERVICE_NAME=$REDIS_SERVICE_NAME
ENV SUBMIT_QUEUE_NAME=$SUBMIT_QUEUE_NAME

RUN pip install redis kubernetes
COPY ./worker.py /worker.py
COPY ./rediswq.py /rediswq.py
COPY ./handle_request.py /handle_request.py

RUN pip install pycryptodome

CMD  python worker.py
