@echo off
echo Starting NOVA BIM Application...
set PYTHONPATH=.
call .\venv\Scripts\activate.bat
python core\app.py
pause
