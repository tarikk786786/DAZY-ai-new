@echo off
title Mark-LVII Assistant
cd /d "C:\Users\tarik\Downloads\FatihMakes\Mark-LVII"
echo Starting Mark-LVII Personal AI Assistant...
"C:\Users\tarik\AppData\Local\Python\pythoncore-3.14-64\python.exe" main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Mark-LVII stopped with error code %ERRORLEVEL%.
    pause
)
