@echo off
REM OpAssist startup script for Windows

echo === OpAssist startup ===

REM Check for .env files
if not exist backend\.env (
    echo ERROR: backend\.env is missing. Copy backend\.env.example and fill in your values.
    exit /b 1
)

if not exist frontend\.env.local (
    echo ERROR: frontend\.env.local is missing. Copy frontend\.env.local.example and fill in your values.
    exit /b 1
)

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
where playwright >nul 2>nul
if errorlevel 1 (
    echo Installing Playwright browsers...
    playwright install chromium
)
cd ..

REM Install frontend dependencies
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo === Setup complete ===
echo.
echo To start the application:
echo   Terminal 1: cd backend ^&^& uvicorn main:app --reload
echo   Terminal 2: cd frontend ^&^& npm run dev
echo.
echo Then open http://localhost:3000
