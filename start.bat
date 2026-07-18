@echo off
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
if exist .env for /f "usebackq tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"
.venv\Scripts\python run.py
