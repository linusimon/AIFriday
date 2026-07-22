@echo off
echo ========================================
echo  Starting Task Routing Frontend (Port 4204)
echo ========================================
echo.

if not exist node_modules (
    echo ERROR: node_modules not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Angular development server on port 4204...
echo Frontend: http://localhost:4204
echo Backend Target: http://localhost:5004
echo.
call npm start

pause
