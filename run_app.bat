@echo off
title Image ^& PDF Converter Studio
cd /d "%~dp0"
echo Starting Image ^& PDF Converter Studio...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error. Check if requirements are installed:
    echo pip install -r requirements.txt
    pause
)
