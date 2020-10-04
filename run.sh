#!/bin/bash -e
/home/mw781/.local/bin/pipenv run gunicorn -w 2  \
    -b unix:/public/home/mw781/web.sock \
    --log-level=info \
    --log-file production.log wsgi:app
