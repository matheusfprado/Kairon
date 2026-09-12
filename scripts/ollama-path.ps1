function Get-KaironOllama {
  $command = Get-Command "ollama" -ErrorAction SilentlyContinue
  if ($null -ne $command) {
    return $command.Source
  }

  $localOllama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
  if (Test-Path $localOllama) {
    return $localOllama
  }

  return $null
}

function Start-KaironOllama {
  param([Parameter(Mandatory = $true)][string]$OllamaPath)

  try {
    Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
    return
  } catch {
    Start-Process -FilePath $OllamaPath -ArgumentList "serve" -WindowStyle Hidden
  }

  for ($attempt = 0; $attempt -lt 15; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
      Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
      return
    } catch {
      continue
    }
  }

  throw "Ollama nao iniciou na porta 11434."
}
