Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 2
$text = [System.Security.SecurityElement]::Escape('Teste de voz do Eilik')
$ssml = '<speak version="1.0" xml:lang="pt-BR" xmlns="http://www.w3.org/2001/10/synthesis"><prosody pitch="+22%" rate="+8%">' + $text + '</prosody></speak>'
Write-Output $ssml
$synth.SpeakSsml($ssml)
