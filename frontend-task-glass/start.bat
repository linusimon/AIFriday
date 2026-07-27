@echo off
echo ========================================
echo  Starting Task Routing Glass Frontend (Port 4205)
echo ========================================
echo.

if not exist node_modules (
    echo ERROR: node_modules not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Angular Glass development server on port 4205...
echo Glass UI: http://localhost:4205
echo Backend Target: http://localhost:5004 (backend-mcp-task)
echo.
call npm start

pause
