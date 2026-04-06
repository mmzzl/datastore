@echo off
cd /d D:\work\datastore\apps\api
py -3.12 -m pytest tests/test_auth.py -v
pause