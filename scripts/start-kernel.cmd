@echo off
rem ChemELLM local kernel launcher (bypasses PowerShell script execution policy).
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv Python. See README.md.
  exit /b 1
)
set CHEMELLM_KERNEL_HOST=127.0.0.1
set CHEMELLM_KERNEL_PORT=8765
if not defined CHEMELLM_DATA_DIR set CHEMELLM_DATA_DIR=%cd%\data\kernel
echo ChemELLM local kernel -^> http://127.0.0.1:%CHEMELLM_KERNEL_PORT%
".venv\Scripts\python.exe" -X utf8 kernel\server.py
endlocal
