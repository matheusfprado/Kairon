function Add-KaironCargoPath {
  $cargoBin = "$env:USERPROFILE\.cargo\bin"
  if ((Test-Path $cargoBin) -and ($env:PATH -notlike "*$cargoBin*")) {
    $env:PATH = "$cargoBin;$env:PATH"
  }
}

function Get-KaironCargo {
  Add-KaironCargoPath

  $command = Get-Command "cargo" -ErrorAction SilentlyContinue
  if ($null -ne $command) {
    return $command.Source
  }

  $cargo = "$env:USERPROFILE\.cargo\bin\cargo.exe"
  if (Test-Path $cargo) {
    return $cargo
  }

  return $null
}
