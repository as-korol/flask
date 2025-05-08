#!/bin/bash
gunicorn --bind 127.0.0.1:5000 wsgi:app & PID=$!
sleep 5
kill -TERM $PID
