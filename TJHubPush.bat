@echo off
:: Quick launcher - runs the app directly from the venv (no build needed)
:: Use this during development or on the same machine where Python is installed.
cd /d "%~dp0"
start "" .venv\Scripts\pythonw.exe hs_app.py
