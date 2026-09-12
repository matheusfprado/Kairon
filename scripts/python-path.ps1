function Get-KaironPython {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python313\python.exe",
    "python",
    "py",
    "python3"
  )

  foreach ($candidate in $candidates) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($null -eq $command) {
      continue
    }

    $source = $command.Source
    if ($source -like "*\Microsoft\WindowsApps\python*.exe") {
      continue
    }

    try {
      & $source --version *> $null
      if ($LASTEXITCODE -eq 0) {
        return $source
      }
    } catch {
      continue
    }
  }

  return $null
}
