@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo Starting CV Layout Cloner Backend
echo ====================================================
echo.

echo Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    echo Waiting for Docker to start (this may take a minute)...
    :check_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        echo Still waiting for Docker...
        goto check_docker
    )
    echo Docker started successfully!
) else (
    echo Docker is already running.
)

echo.
echo Building and starting the app...
docker-compose down
docker-compose up -d --build

echo.
echo ====================================================
echo The backend is now running locally at:
echo http://localhost:8080
echo ====================================================
echo.
echo Connecting Ngrok tunnel...
echo (Press Ctrl+C to close the tunnel and stop the backend)
echo.

:: Add authtoken just in case it's not saved globally
call npx ngrok config add-authtoken 3GGpPjz8kUW54sAf1QqH1rHKyD7_7C4KaHhe2rcY17Wh2f5xX

:: Start Ngrok on port 8080 using the static domain
npx ngrok http --domain=decorated-cognition-aspire.ngrok-free.dev 8080
