@echo off
rem Starts Lycantrope from the project's virtual environment. Extra arguments are passed through.
"%~dp0.venv\Scripts\python.exe" -m lycantrope %*
