@echo off
REM VoxTrace Startup Script for Windows

echo Starting VoxTrace...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check if Docker is available
docker ps >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)

REM Start PostgreSQL
echo Starting PostgreSQL with Docker Compose...
docker-compose up -d

REM Wait for PostgreSQL
echo Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

REM Create audio storage directory
if not exist "audio_storage" mkdir audio_storage

echo.
echo VoxTrace is ready!
echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Start the application
python main.py
