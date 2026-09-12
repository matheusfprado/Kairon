import asyncio
import re
import subprocess

from core.voice.tts.base import TextToSpeechProvider


class WindowsTextToSpeechProvider(TextToSpeechProvider):
    def __init__(self, voice: str = "Microsoft David Desktop", rate: str = "+5%", pitch: str = "-12%") -> None:
        self.voice = voice
        self.rate = rate if re.fullmatch(r"[+-]?\d+%", rate) else "+5%"
        self.pitch = pitch if re.fullmatch(r"[+-]?\d+%", pitch) else "-12%"

    async def speak(self, text: str) -> None:
        escaped = text.replace("'", "''")
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$preferred = $synth.GetInstalledVoices() | "
            "Where-Object { $_.VoiceInfo.Name -eq '" + self.voice.replace("'", "''") + "' } | Select-Object -First 1; "
            "$male = $synth.GetInstalledVoices() | "
            "Where-Object { $_.VoiceInfo.Gender -eq 'Male' } | Select-Object -First 1; "
            "$female = $synth.GetInstalledVoices() | "
            "Where-Object { $_.VoiceInfo.Gender -eq 'Female' } | Select-Object -First 1; "
            "if ($preferred) { $synth.SelectVoice($preferred.VoiceInfo.Name) } elseif ($male) { $synth.SelectVoice($male.VoiceInfo.Name) } elseif ($female) { $synth.SelectVoice($female.VoiceInfo.Name) }; "
            "$synth.Rate = 2; "
            "$text = [System.Security.SecurityElement]::Escape('" + escaped + "'); "
            "$ssml = '<speak version=\"1.0\" xml:lang=\"pt-BR\" xmlns=\"http://www.w3.org/2001/10/synthesis\"><prosody pitch=\"" + self.pitch + "\" rate=\"" + self.rate + "\">' + "
            "$text + '</prosody></speak>'; "
            "$synth.SpeakSsml($ssml);"
        )
        await asyncio.to_thread(
            subprocess.run,
            ["powershell", "-NoProfile", "-Command", command],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
