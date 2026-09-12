import os

from faster_whisper import WhisperModel

model_name = os.getenv("KAIRON_STT_MODEL", "small")
print(f"Preparando modelo de voz local: {model_name}")
WhisperModel(model_name, device="cpu", compute_type="int8")
print("Modelo de voz pronto.")
