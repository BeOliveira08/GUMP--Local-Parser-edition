@echo off
setlocal enabledelayedexpansion

REM Ajusta pro diretório do .bat
cd /d "%~dp0"

REM Checa python
python --version >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado no PATH.
  echo Instala o Python 3.10+ e marca "Add Python to PATH".
  pause
  exit /b 1
)

REM Cria venv se nao existir
if not exist ".venv\" (
  echo Criando virtualenv...
  python -m venv .venv
)

REM Ativa venv
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo Falha ativando venv.
  pause
  exit /b 1
)

REM Atualiza pip
python -m pip install --upgrade pip

REM Instala deps (se requirements.txt existir)
if exist "requirements.txt" (
  echo Instalando dependencias do requirements.txt...
  pip install -r requirements.txt
) else (
  echo requirements.txt nao encontrado. Instalando deps minimas...
  pip install pdfplumber python-docx beautifulsoup4
)

REM Roda o app
echo Iniciando GUMP...
python app.py

endlocal