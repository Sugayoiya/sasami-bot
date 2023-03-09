FROM python:3.9 as requirements-stage

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /app

COPY ./ /app/

RUN apt-get update && apt-get install -y build-essential cmake --no-install-recommends && apt-get install -y ffmpeg

RUN /usr/local/bin/python -m pip install  --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir --upgrade -r requirements.txt

VOLUME /app/accounts /app/data