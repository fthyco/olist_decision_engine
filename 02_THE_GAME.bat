@echo off
title Olist Simulator GUI
echo Launching Application...

cd generator_app

python training_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo -----------------------------------
    echo ERROR: The application crashed.
    echo -----------------------------------
    pause
)