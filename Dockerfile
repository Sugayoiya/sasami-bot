FROM python:3.9 as requirements-stage

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /app

COPY ./ /app/

RUN /usr/local/bin/python -m pip install  --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir --upgrade -r requirements.txt

VOLUME /app/accounts /app/data