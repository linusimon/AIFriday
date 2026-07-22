@echo off
echo Setting up Intelligent Task Routing Backend...

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
if not exist uploads mkdir uploads
if not exist faiss_index mkdir faiss_index
if not exist data mkdir data

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Update .env file with your API keys
echo 2. Run start.bat to start the server
echo.
pause
