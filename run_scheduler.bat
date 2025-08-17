@echo off
echo =====================================
echo 988 SCHEDULER SYSTEM
echo =====================================
echo.
echo This will start the automated scheduler.
echo Tasks will run at their scheduled times.
echo.
echo Press any key to start...
pause > nul

cd /d "%~dp0"
python start_scheduler.py

pause