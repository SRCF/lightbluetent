FROM python:3.8-buster

ENV PYTHONUNBUFFERED 1

RUN mkdir /opt/code && mkdir /opt/requirements
WORKDIR /opt/code

ADD requirements /opt/requirements
RUN python3 -m pip install -r /opt/requirements/development.txt