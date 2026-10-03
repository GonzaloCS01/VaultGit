$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host ""
Write-Host "VaultGit 1.0.0 - Release Build"
Write-Host "==============================="
Write-Host ""

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "No se encontro el entorno virtual .venv."
}

Write-Host "[1/5] Ejecutando pruebas..."
& ".\.venv\Scripts\python.exe" -m pytest -q

Write-Host ""
Write-Host "[2/5] Limpiando builds anteriores..."
Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\dist" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "[3/5] Construyendo VaultGit.exe..."
& ".\.venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    ".\packaging\VaultGit.spec"

Write-Host ""
Write-Host "[4/5] Verificando ejecutable..."
$ExePath = ".\dist\VaultGit.exe"

if (-not (Test-Path $ExePath)) {
    throw "La compilacion termino sin producir dist\VaultGit.exe."
}

$Exe = Get-Item $ExePath

Write-Host "Ejecutable:"
Write-Host $Exe.FullName
Write-Host ""

Write-Host "Tamaño:"
Write-Host ("{0:N2} MB" -f ($Exe.Length / 1MB))
Write-Host ""

Write-Host "SHA-256:"
(Get-FileHash $ExePath -Algorithm SHA256).Hash

Write-Host ""
Write-Host "[5/5] Build completado correctamente."
Write-Host ""
Write-Host "IMPORTANTE:"
Write-Host "- La boveda NO esta incluida en el ejecutable."
Write-Host "- Los backups NO estan incluidos en el ejecutable."
Write-Host "- Prueba dist\VaultGit.exe antes de distribuirlo."
