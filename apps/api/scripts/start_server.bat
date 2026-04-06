@echo off
cd /d D:\work\datastore\apps\api
py -3.12 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload