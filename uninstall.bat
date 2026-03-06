@echo off
REM Desinstalador do GUMP
REM Este script remove o GUMP do computador

setlocal enabledelayedexpansion

REM Cores (aproximadas no CMD)
cls
echo.
echo ========================================
echo       DESINSTALADOR GUMP
echo ========================================
echo.

REM Pergunta confirmacao
echo Tem certeza que deseja desinstalar o GUMP?
echo.
set /p confirm="Digite 'sim' para confirmar: "

if /i not "%confirm%"=="sim" (
    echo Desinstalacao cancelada.
    pause
    exit /b 0
)

echo.
echo Iniciando desinstalacao...
echo.

REM Para o processo GUMP.exe se estiver rodando
echo [*] Fechando GUMP se estiver rodando...
taskkill /IM GUMP.exe /F 2>nul
taskkill /IM app.exe /F 2>nul

echo [*] Removendo arquivos...
REM Remove a pasta dist (contem GUMP.exe)
if exist "dist\" (
    rmdir /s /q "dist\" 2>nul
    echo     - Removido: pasta dist
)

REM Remove build files do PyInstaller
if exist "build\" (
    rmdir /s /q "build\" 2>nul
    echo     - Removido: pasta build
)

if exist "app.spec" (
    del /q "app.spec" 2>nul
    echo     - Removido: app.spec
)

REM Remove atalhos do Desktop (se existirem)
if exist "%USERPROFILE%\Desktop\GUMP.lnk" (
    del /q "%USERPROFILE%\Desktop\GUMP.lnk" 2>nul
    echo     - Removido: atalho do Desktop
)

REM Remove atalhos do Menu Iniciar (se existirem)
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\GUMP.lnk" (
    del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\GUMP.lnk" 2>nul
    echo     - Removido: atalho do Menu Iniciar
)

echo.
echo ========================================
echo     DESINSTALACAO CONCLUIDA!
echo ========================================
echo.
pause
endlocal
