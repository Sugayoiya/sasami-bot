FROM python:3.10 as requirements-stage

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

WORKDIR /app

COPY ./ /app/

RUN /usr/local/bin/python -m pip install  --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir --upgrade -r requirements.txt

VOLUME /app/accounts /app/data