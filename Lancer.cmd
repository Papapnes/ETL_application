@echo off
setlocal
cd /d "%~dp0"
title DataFlow Studio - Lancement
set "UV_CACHE_DIR=%CD%\.uv-cache"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv est requis. Consultez README.md pour l'installation.
  pause
  exit /b 1
)
uv sync --locked
if errorlevel 1 (
  echo Installation impossible. Verifiez votre connexion et consultez README.md.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\launch.py"
if errorlevel 1 (
  echo Le lancement a echoue. Consultez le message ci-dessus.
)
pause

