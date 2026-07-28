@echo off
echo Starting Intelligent Task Routing Backend...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Flask application and background SQLite MCP Server
echo Starting Task Routing Platform (Backend port 5004, MCP port 5001)...
python run_app.py

pause
