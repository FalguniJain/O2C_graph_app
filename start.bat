@echo off
echo =============================================
echo   O2C Graph - Order to Cash Analytics
echo =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js from nodejs.org
    pause
    exit /b 1
)

:: Check API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo IMPORTANT: Set your Anthropic API key first!
    echo.
    set /p ANTHROPIC_API_KEY="Enter your Anthropic API key (sk-ant-...): "
    setx ANTHROPIC_API_KEY "%ANTHROPIC_API_KEY%" >nul
)

echo.
echo [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt -q
cd ..

echo [2/3] Installing frontend dependencies...
cd frontend
if not exist node_modules (
    npm install -q
)
cd ..

echo [3/3] Starting servers...
echo.
echo Backend will start on: http://localhost:5000
echo Frontend will start on: http://localhost:5173
echo.
echo Opening app in browser in 5 seconds...
echo Press Ctrl+C in either window to stop.
echo.

:: Start backend
start "O2C Backend" cmd /k "cd backend && python app.py"

:: Wait a moment then start frontend
timeout /t 3 /nobreak >nul
start "O2C Frontend" cmd /k "cd frontend && npm run dev"

:: Open browser
timeout /t 5 /nobreak >nul
start http://localhost:5173
