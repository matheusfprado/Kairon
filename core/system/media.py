import ctypes
import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

from core.memory.extractor import normalize_text

MediaAction = Literal[
    "pause",
    "resume",
    "next",
    "previous",
    "search_play",
    "volume_up",
    "volume_down",
    "volume_set",
    "mute",
]
SpotifyContentType = Literal["track", "playlist"]


@dataclass(frozen=True)
class MediaCommand:
    action: MediaAction
    query: str | None = None
    volume: int | None = None
    content_type: SpotifyContentType = "track"


class SpotifyControlError(RuntimeError):
    pass


class SpotifyController:
    pause_phrases = ("pause", "pausar", "pare a musica", "parar a musica", "pare a faixa")
    resume_phrases = (
        "continue a musica",
        "continuar a musica",
        "continuar musica",
        "dar play",
        "reproduza musica",
        "reproduzir musica",
        "toque musica",
    )
    next_phrases = (
        "avancar musica",
        "proxima faixa",
        "proxima musica",
        "pula musica",
        "pule a faixa",
        "pule a musica",
        "pular a musica",
        "pular musica",
    )
    previous_phrases = (
        "faixa anterior",
        "musica anterior",
        "volte a musica",
        "voltar musica",
    )
    search_play_pattern = re.compile(
        r"\b(?:toque|tocar|reproduza|reproduzir|coloque|colocar|bote|botar)\b\s+(.+)",
        re.IGNORECASE,
    )
    search_pattern = re.compile(
        r"\b(?:pesquise|pesquisar|procure|procurar)\b\s+(.+)",
        re.IGNORECASE,
    )
    playlist_pattern = re.compile(
        r"\b(?:quero|toque|tocar|reproduza|reproduzir|coloque|colocar|bote|botar|"
        r"pesquise|pesquisar|procure|procurar)\b.*?\bplaylist\b(?:\s+de)?\s+(.+)",
        re.IGNORECASE,
    )
    volume_pattern = re.compile(r"\bvolume\s+(?:em|para)?\s*(\d{1,3})\s*%?")

    media_keys: ClassVar[dict[MediaAction, int]] = {
        "pause": 0xB3,
        "resume": 0xB3,
        "next": 0xB0,
        "previous": 0xB1,
        "volume_up": 0xAF,
        "volume_down": 0xAE,
        "mute": 0xAD,
    }

    def __init__(
        self,
        cli_runner: Callable[[tuple[str, ...]], str] | None = None,
        key_sender: Callable[[int, int], None] | None = None,
        sleeper: Callable[[float], None] | None = None,
        app_starter: Callable[[], None] | None = None,
    ) -> None:
        self.cli_path = self._find_cli()
        self.cli_runner = cli_runner or self._run_cli
        self.key_sender = key_sender or self._send_media_key
        self.sleeper = sleeper or time.sleep
        self.app_starter = app_starter or (
            self._launch_spotify_app if cli_runner is None else lambda: None
        )

    @property
    def available(self) -> bool:
        return self.cli_path is not None

    def parse(self, text: str) -> MediaCommand | None:
        normalized = normalize_text(text).strip(" ,.!?")

        playlist_match = self.playlist_pattern.search(normalized)
        if playlist_match:
            query = self._clean_playlist_query(playlist_match.group(1))
            if query:
                return MediaCommand("search_play", query=query, content_type="playlist")

        volume_match = self.volume_pattern.search(normalized)
        if volume_match:
            volume = min(100, int(volume_match.group(1)))
            return MediaCommand("volume_set", volume=volume)
        if any(phrase in normalized for phrase in ("volume maximo", "volume no maximo")):
            return MediaCommand("volume_set", volume=100)
        if any(phrase in normalized for phrase in ("aument", "suba")) and self._mentions_volume(
            normalized
        ):
            return MediaCommand("volume_up")
        if any(phrase in normalized for phrase in ("abaix", "diminu", "reduz")) and (
            self._mentions_volume(normalized)
        ):
            return MediaCommand("volume_down")
        if any(phrase in normalized for phrase in ("silencie", "silenciar", "mudo", "mute")):
            return MediaCommand("mute")

        if any(phrase in normalized for phrase in self.next_phrases):
            return MediaCommand("next")
        if any(phrase in normalized for phrase in self.previous_phrases):
            return MediaCommand("previous")
        if any(phrase in normalized for phrase in self.pause_phrases):
            return MediaCommand("pause")
        play_match = self.search_play_pattern.search(normalized)
        if play_match:
            query = self._clean_query(play_match.group(1))
            if query:
                return MediaCommand("search_play", query=query)

        if any(phrase in normalized for phrase in self.resume_phrases):
            return MediaCommand("resume")

        search_match = self.search_pattern.search(normalized)
        if search_match and any(
            marker in normalized
            for marker in ("spotify", "musica", "faixa", "e reproduz", "e toqu")
        ):
            query = self._clean_query(search_match.group(1))
            if query:
                return MediaCommand("search_play", query=query)
        return None

    def execute(self, command: MediaCommand) -> str:
        if command.action == "search_play":
            return self._search_and_play(command.query or "", command.content_type)
        if command.action == "volume_set":
            volume = command.volume or 0
            self._spotify_command(("volume", f"{volume / 100:.2f}"))
            return f"Volume do Spotify ajustado para {volume} por cento."
        if command.action in {"volume_up", "volume_down", "mute"}:
            presses = 3 if command.action in {"volume_up", "volume_down"} else 1
            self.key_sender(self.media_keys[command.action], presses)
            responses = {
                "volume_up": "Aumentei o volume do computador.",
                "volume_down": "Diminu\u00ed o volume do computador.",
                "mute": "Alternei o sil\u00eancio do computador.",
            }
            return responses[command.action]

        used_fallback = False
        try:
            self._spotify_command((command.action,))
        except SpotifyControlError:
            self.key_sender(self.media_keys[command.action], 1)
            used_fallback = True
        if used_fallback and command.action in {"pause", "resume"}:
            return "Alternei a reprodu\u00e7\u00e3o pelo controle de m\u00eddia do Windows."
        responses = {
            "pause": "M\u00fasica pausada.",
            "resume": "Continuando a reprodu\u00e7\u00e3o.",
            "next": "Pulando para a pr\u00f3xima m\u00fasica.",
            "previous": "Voltando para a m\u00fasica anterior.",
        }
        return responses[command.action]

    def _search_and_play(self, query: str, content_type: SpotifyContentType) -> str:
        search = self._spotify_command(
            ("search", query, "--type", content_type, "--limit", "1", "--format", "json")
        )
        try:
            collection_name = "tracks" if content_type == "track" else "playlists"
            items = json.loads(search).get(collection_name, [])
            item = items[0]
            uri = str(item["uri"])
            name = str(item["name"])
            artists = ", ".join(str(artist) for artist in item.get("artists", []))
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
            content_label = "playlist" if content_type == "playlist" else "m\u00fasica"
            raise SpotifyControlError(f"N\u00e3o encontrei a {content_label} {query}.") from exc

        self._spotify_command(("play", uri))
        suffix = f" de {artists}" if artists else ""
        content_label = "playlist " if content_type == "playlist" else ""
        return f"Reproduzindo {content_label}{name}{suffix} no Spotify."

    def _spotify_command(self, arguments: tuple[str, ...]) -> str:
        try:
            return self.cli_runner(arguments)
        except SpotifyControlError as first_error:
            if arguments[0] == "open":
                raise
            try:
                self.app_starter()
                self.cli_runner(("open",))
            except (OSError, SpotifyControlError) as open_error:
                raise SpotifyControlError(str(open_error)) from first_error

            retry_error: SpotifyControlError = first_error
            for _ in range(6):
                self.sleeper(2)
                try:
                    return self.cli_runner(arguments)
                except SpotifyControlError as exc:
                    retry_error = exc
            raise SpotifyControlError(str(retry_error)) from first_error

    @staticmethod
    def _clean_query(value: str) -> str:
        query = re.sub(
            r"^(?:e\s+)?(?:toque|tocar|reproduza|reproduzir)?\s*"
            r"(?:(?:a|uma)\s+)?(?:musica|faixa)\s*",
            "",
            value,
        )
        query = re.sub(r"\s+(?:no|do|pelo)\s+spotify\b", "", query)
        query = re.sub(r"\s+e\s+(?:toque|reproduza|coloque)$", "", query)
        query = re.sub(r"^(?:do|da|de)\s+", "", query)
        return re.sub(r"\s+por favor$", "", query).strip(" ,.!?")

    @staticmethod
    def _clean_playlist_query(value: str) -> str:
        query = re.sub(r"\s+(?:no|do|pelo)\s+spotify\b", "", value)
        return re.sub(r"\s+por favor$", "", query).strip(" ,.!?")

    @staticmethod
    def _mentions_volume(value: str) -> bool:
        return any(term in value for term in ("volume", "voulome", "som"))

    def _run_cli(self, arguments: tuple[str, ...]) -> str:
        if self.cli_path is None:
            raise SpotifyControlError("Spotify CLI nao foi encontrado.")
        try:
            result = subprocess.run(
                (self.cli_path, *arguments),
                check=True,
                capture_output=True,
                encoding="utf-8",
                timeout=20,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise SpotifyControlError(str(detail).strip()) from exc
        return result.stdout.strip()

    @staticmethod
    def _find_cli() -> str | None:
        discovered = shutil.which("spotify_cli.exe")
        if discovered:
            return discovered
        alias = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "spotify_cli.exe"
        return str(alias) if alias.exists() else None

    @staticmethod
    def _launch_spotify_app() -> None:
        spotify = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "Spotify.exe"
        subprocess.Popen(
            (str(spotify),),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _send_media_key(virtual_key: int, presses: int) -> None:
        user32 = ctypes.windll.user32
        for _ in range(presses):
            user32.keybd_event(virtual_key, 0, 0, 0)
            user32.keybd_event(virtual_key, 0, 0x0002, 0)
