@echo off
cd /d D:\work\datastore\frontend\vue-admin
start "Frontend" cmd /c "npm run dev"
timeout /t 15 /nobreak
python "D:\work\datastore\frontend\vue-admin\tests\integration_runner.py"
echo.
echo Press any key to exit...
pause >nul