FROM python:3.8-buster

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/code/

RUN python -m pip install pipenv

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install

COPY . .
