#!/bin/bash -e
exec gunicorn -w 2 -b unix:/home/mw781/lightbluetent/web.sock \
    --log-file - --log-level debug wsgi:app