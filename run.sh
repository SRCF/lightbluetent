#!/bin/bash -e

pipenv run

PYTHONPATH=~/lightbluetent/lightbluetent:$PYTHONPATH \
    exec gunicorn -w 2 -b unix:/home/mw781/lightbluetent/web.sock \
    --log-file - wsgi:app