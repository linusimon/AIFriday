@echo off
echo Starting Intelligent Task Routing Backend...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Flask application
echo Starting Flask server on port 5004...
python app.py

pause
