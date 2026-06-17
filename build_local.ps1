# Script para replicar localmente el flujo de GitHub Actions (build_students.yml)
# Ejecutar desde la raíz del proyecto: .\build_local.ps1

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Iniciando Replicación de Despliegue Local (Zoho Survey) " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Verificar Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python no está instalado o no está en el PATH." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "[INFO] Utilizando: $pythonVersion" -ForegroundColor Green

# 2. Instalar Dependencias
Write-Host "`n[INFO] Instalando dependencias de requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Falló la instalación de dependencias." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Descargar Modelo NLP de Spacy
Write-Host "`n[INFO] Descargando modelo NLP en español (es_core_news_sm)..." -ForegroundColor Yellow
python -m spacy download es_core_news_sm

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Falló la descarga del modelo de Spacy." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 4. Generar Archivos JSON (ETL)
Write-Host "`n[INFO] Ejecutando el pipeline ETL (scripts/build_json.py)..." -ForegroundColor Yellow
Write-Host "       Esto procesará los CSV en /data y generará los JSONs estáticos." -ForegroundColor Gray
python zoho-survey/scripts/build_json.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] El script de generación de JSON falló. Revisa los logs de Python arriba." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Finalización exitosa
Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " Construcción Local Finalizada Exitosamente " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Puedes validar los cambios ejecutando:" -ForegroundColor Gray
Write-Host "  python -m http.server 8000" -ForegroundColor White
Write-Host "Y accediendo a: http://localhost:8000/zoho-survey/" -ForegroundColor White
