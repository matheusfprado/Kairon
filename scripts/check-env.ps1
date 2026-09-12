$ErrorActionPreference = "Stop"

. "$PSScriptRoot\python-path.ps1"
. "$PSScriptRoot\rust-path.ps1"
. "$PSScriptRoot\ollama-path.ps1"

function Test-Command($Name) {
  $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

$missing = New-Object System.Collections.Generic.List[string]

if (-not (Test-Command "node")) {
  $missing.Add("Node.js")
}

if (-not (Test-Command "pnpm")) {
  $missing.Add("pnpm")
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  if ($null -eq (Get-KaironPython)) {
    $missing.Add("Python")
  } else {
    $missing.Add("Python venv (.venv)")
  }
}

if ($null -eq (Get-KaironCargo)) {
  $missing.Add("Rust/Cargo")
}

if ($null -eq (Get-KaironOllama)) {
  $missing.Add("Ollama")
}

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host "Kairon nao pode iniciar ainda. Faltando:" -ForegroundColor Yellow
  foreach ($item in $missing) {
    Write-Host " - $item" -ForegroundColor Yellow
  }
  Write-Host ""
  Write-Host "Instale as dependencias, reabra o PowerShell, depois rode:" -ForegroundColor Cyan
  Write-Host "winget install Python.Python.3.12"
  Write-Host "winget install Rustlang.Rustup"
  Write-Host "winget install Ollama.Ollama"
  Write-Host "pnpm setup:python"
  Write-Host "pnpm dev"
  Write-Host ""
  Write-Host "Para abrir apenas a interface web sem Tauri/Core:" -ForegroundColor Cyan
  Write-Host "pnpm dev:web"
  exit 1
}

Write-Host "Ambiente Kairon OK." -ForegroundColor Green
