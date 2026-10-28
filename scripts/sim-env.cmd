@echo off
rem Open a PowerShell with the simulation environment (IDAES solvers + .venv-sim) ready.
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0sim-env.ps1"
