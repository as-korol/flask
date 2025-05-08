gunicorn --bind 127.0.0.1:5000 app:app & APP_PID=$!
sleep 20
python3 client.py
CLIENT_CODE=$?
sleep 5
kill -TERM $APP_PID
exit $CLIENT_CODE