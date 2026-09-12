$ErrorActionPreference = "Stop"

. "$PSScriptRoot\rust-path.ps1"
. "$PSScriptRoot\ollama-path.ps1"
Add-KaironCargoPath

pnpm check:env
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$ollama = Get-KaironOllama
Start-KaironOllama -OllamaPath $ollama

pnpm --filter @kairon/desktop tauri
exit $LASTEXITCODE
