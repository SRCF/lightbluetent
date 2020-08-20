#!/bin/bash -e
PIPENV_DONT_LOAD_ENV=1 /home/mw781/.local/bin/pipenv run gunicorn -w 2  \
    -b unix:/public/home/mw781/web.sock \
    --log-file production.log --log-level debug wsgi:app
