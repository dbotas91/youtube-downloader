# Script PowerShell para iniciar o YouTube Downloader no Windows
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       YouTube Channel Downloader & Inventory           " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Python não foi encontrado no sistema!" -ForegroundColor Red
    Write-Host "Por favor instala o Python 3.10+ de https://www.python.org/downloads/"
    Write-Host "Lembra-te de marcar a opção 'Add Python to PATH' na instalação."
    Read-Host "Pressiona Enter para sair..."
    exit 1
}

# 2. Verificar/Criar .venv
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "A configurar ambiente virtual Python (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
    & .venv\Scripts\python.exe -m pip install --upgrade pip
    & .venv\Scripts\pip.exe install -r requirements.txt
}

# 3. Verificar FFmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "[AVISO] FFmpeg não foi encontrado no PATH do Windows." -ForegroundColor Yellow
    Write-Host "Recomenda-se instalar com: winget install Gyan.FFmpeg" -ForegroundColor Gray
    Write-Host ""
}

# 4. Executar
& .venv\Scripts\python.exe main.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nA aplicação terminou com código de erro $LASTEXITCODE." -ForegroundColor Red
    Read-Host "Pressiona Enter para sair..."
}
