Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.GetInstalledVoices() | ForEach-Object { $v=$_.VoiceInfo; Write-Output ("{0}|{1}|{2}" -f $v.Name,$v.Gender,$v.Culture) }
