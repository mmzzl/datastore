@echo off
REM Integration Test Runner for Datastore API
REM Run: scripts\run-integration-tests.bat

echo Running integration tests...
echo.

py -3.12 -m pytest apps/api/tests/integration/ -v

if %ERRORLEVEL% neq 0 (
    echo.
    echo Tests failed!
    exit /b 1
)

echo.
echo All integration tests passed!
