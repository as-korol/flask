cd /home/flask_brightness/flaskapp

cat > wsgi.py << 'EOF'
from some_app import app

if __name__ == "__main__":
    app.run()
EOF

ls -la wsgi.py