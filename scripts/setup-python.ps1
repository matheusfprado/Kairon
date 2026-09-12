$ErrorActionPreference = "Stop"

. "$PSScriptRoot\python-path.ps1"
. "$PSScriptRoot\ollama-path.ps1"

$python = Get-KaironPython
if ($null -eq $python) {
  Write-Host "Python nao encontrado." -ForegroundColor Yellow
  Write-Host "Instale e reabra o PowerShell:"
  Write-Host "winget install Python.Python.3.12"
  exit 1
}

if (-not (Test-Path ".\.venv")) {
  & $python -m venv .venv
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

.\.venv\Scripts\python.exe scripts\setup-stt.py
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$ollama = Get-KaironOllama
if ($null -eq $ollama) {
  Write-Host "Ollama nao encontrado. Instale com:" -ForegroundColor Yellow
  Write-Host "winget install Ollama.Ollama"
  exit 1
}

Start-KaironOllama -OllamaPath $ollama
$ollamaModel = if ($env:KAIRON_OLLAMA_MODEL) { $env:KAIRON_OLLAMA_MODEL } else { "llama3.2:3b" }
& $ollama show $ollamaModel *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Baixando modelo Ollama: $ollamaModel" -ForegroundColor Cyan
  & $ollama pull $ollamaModel
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

$embeddingModel = if ($env:KAIRON_KNOWLEDGE_EMBEDDING_MODEL) {
  $env:KAIRON_KNOWLEDGE_EMBEDDING_MODEL
} else {
  "nomic-embed-text-v2-moe"
}
& $ollama show $embeddingModel *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Baixando modelo de conhecimento: $embeddingModel" -ForegroundColor Cyan
  & $ollama pull $embeddingModel
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

Write-Host "Ambiente Python pronto." -ForegroundColor Green
