@echo off
cd /d "e:\Program Files\CfpaZMS"
set FLASK_APP=app:create_app
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5001