@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python install_autostart.py
python checker.py
