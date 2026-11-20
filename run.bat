@echo off
chcp 65001 >nul
title YouTube Channel Downloader

echo ========================================================
echo        YouTube Channel Downloader ^& Inventory
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Verificar se o Python está instalado
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRO] O Python nao foi encontrado no sistema!
    echo.
    echo Por favor instala o Python 3.10 ou superior a partir de:
    echo   https://www.python.org/downloads/
    echo Certifica-te de marcar a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

:: 2. Verificar ou criar o ambiente virtual (.venv)
if not exist ".venv\Scripts\python.exe" (
    echo A configurar o ambiente virtual (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual Python.
        pause
        exit /b 1
    )
    echo A instalar dependencias necessarias...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha ao instalar dependencias do requirements.txt.
        pause
        exit /b 1
    )
) else (
    call .venv\Scripts\activate.bat
)

:: 3. Verificar FFmpeg (aviso informativo)
where ffmpeg >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [AVISO] FFmpeg nao foi encontrado no PATH do Windows.
    echo Para combinar video e audio em MP4 com maxima qualidade, instala o FFmpeg:
    echo   winget install Gyan.FFmpeg
    echo.
)

:: 4. Executar a aplicacao
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo A aplicacao terminou com codigo de erro %ERRORLEVEL%.
    pause
)
