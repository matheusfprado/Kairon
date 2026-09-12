import json
import logging
import os
import re
import subprocess
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import ClassVar, Literal

from core.memory.extractor import normalize_text
from core.security.permissions import PermissionGuard, RiskLevel, StructuredIntent

logger = logging.getLogger("SYSTEM")

TargetKind = Literal["process", "path", "url", "start_app"]
AppCatalog = dict[str, tuple[str, str]]


@dataclass(frozen=True)
class ComputerTarget:
    kind: TargetKind
    value: str | tuple[str, ...]
    label: str


@dataclass(frozen=True)
class ComputerCommand:
    intent: StructuredIntent
    target: ComputerTarget | None = None


class ComputerController:
    _cached_start_apps: ClassVar[AppCatalog | None] = None
    blocked_terms = (
        "apag",
        "cmd",
        "delete",
        "desinstal",
        "deslig",
        "exclu",
        "format",
        "powershell",
        "prompt de comando",
        "reinici",
        "rode um comando",
        "terminal",
    )
    blocked_application_terms = blocked_terms + (
        "agendador de tarefas",
        "editor de registro",
        "editor do registro",
        "gerenciamento do computador",
        "politica de seguranca local",
        "servicos do windows",
    )
    open_pattern = re.compile(
        r"\b(?:abra|abre|abrir|inicie|iniciar|mostre|acesse|va para)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        process_launcher: Callable[[tuple[str, ...]], None] | None = None,
        path_launcher: Callable[[str], None] | None = None,
        url_launcher: Callable[[str], object] | None = None,
        app_launcher: Callable[[str], None] | None = None,
        app_catalog_provider: Callable[[], AppCatalog] | None = None,
    ) -> None:
        home = Path.home()
        self.targets = {
            "bloco de notas": ComputerTarget("process", ("notepad.exe",), "Bloco de Notas"),
            "calculadora": ComputerTarget("process", ("calc.exe",), "Calculadora"),
            "explorador de arquivos": ComputerTarget(
                "process", ("explorer.exe",), "Explorador de Arquivos"
            ),
            "explorador": ComputerTarget("process", ("explorer.exe",), "Explorador de Arquivos"),
            "configuracoes": ComputerTarget("path", "ms-settings:", "Configuracoes"),
            "meus documentos": ComputerTarget("path", str(home / "Documents"), "Documentos"),
            "documentos": ComputerTarget("path", str(home / "Documents"), "Documentos"),
            "downloads": ComputerTarget("path", str(home / "Downloads"), "Downloads"),
            "area de trabalho": ComputerTarget("path", str(home / "Desktop"), "Area de Trabalho"),
            "imagens": ComputerTarget("path", str(home / "Pictures"), "Imagens"),
            "musicas": ComputerTarget("path", str(home / "Music"), "Musicas"),
            "navegador": ComputerTarget("url", "https://www.google.com", "Navegador"),
            "google": ComputerTarget("url", "https://www.google.com", "Google"),
            "youtube": ComputerTarget("url", "https://www.youtube.com", "YouTube"),
            "gmail": ComputerTarget("url", "https://mail.google.com", "Gmail"),
        }
        self.guard = PermissionGuard()
        self.process_launcher = process_launcher or self._launch_process
        self.path_launcher = path_launcher or self._open_path
        self.url_launcher = url_launcher or webbrowser.open
        self.app_launcher = app_launcher or self._launch_start_app
        self.apps = (app_catalog_provider or self._start_apps)()
        logger.info("computer_apps_indexed count=%s", len(self.apps))

    @property
    def available_app_count(self) -> int:
        return len(self.apps)

    def parse(self, text: str) -> ComputerCommand | None:
        normalized = normalize_text(text)
        for term in self.blocked_terms:
            if term in normalized:
                return self._blocked_command(term)

        match = self.open_pattern.search(normalized)
        if match is None:
            requested = self._direct_target(normalized)
            app = self.apps.get(requested)
            if app is not None:
                return self._application_command(*app)
            target = self.targets.get(requested)
            if target is not None:
                return self._target_command(target)
            return None

        requested = self._requested_target(normalized[match.end() :])
        if not requested:
            return self._not_found_command("aplicativo")

        app = self.apps.get(requested)
        if app is not None:
            return self._application_command(*app)

        target = self.targets.get(requested)
        if target is not None:
            return self._target_command(target)

        for alias in sorted(self.targets, key=len, reverse=True):
            if re.search(rf"\b{re.escape(alias)}\b", requested):
                return self._target_command(self.targets[alias])

        app = self._closest_application(requested)
        if app is not None:
            return self._application_command(*app)
        return self._not_found_command(requested)

    def execute(self, command: ComputerCommand) -> str:
        if not self.guard.validate(command.intent) or command.target is None:
            raise PermissionError("Esta acao exige autorizacao e nao foi executada.")

        target = command.target
        if target.kind == "process":
            assert isinstance(target.value, tuple)
            self.process_launcher(target.value)
        elif target.kind == "path":
            assert isinstance(target.value, str)
            self.path_launcher(target.value)
        elif target.kind == "url":
            assert isinstance(target.value, str)
            self.url_launcher(target.value)
        else:
            assert isinstance(target.value, str)
            self.app_launcher(target.value)
        return target.label

    def _closest_application(self, requested: str) -> tuple[str, str] | None:
        candidates: list[tuple[float, int, str, str]] = []
        for normalized_name, (label, app_id) in self.apps.items():
            if requested in normalized_name or normalized_name in requested:
                score = 1.0
            else:
                score = SequenceMatcher(None, requested, normalized_name).ratio()
            if score >= 0.78:
                candidates.append((score, len(normalized_name), label, app_id))
        if not candidates:
            return None
        _, _, label, app_id = max(candidates)
        return label, app_id

    def _application_command(self, label: str, app_id: str) -> ComputerCommand:
        normalized_app = normalize_text(f"{label} {app_id}")
        if any(term in normalized_app for term in self.blocked_application_terms):
            return self._blocked_command(label)
        return self._target_command(ComputerTarget("start_app", app_id, label))

    @staticmethod
    def _requested_target(value: str) -> str:
        requested = re.sub(
            r"^(?:para mim\s+)?(?:(?:o|a|os|as|meu|minha)\s+)?(?:app|aplicativo|pasta\s+)?",
            "",
            value.strip(" ,.!?"),
        )
        return re.sub(r"\s+(?:agora|por favor)$", "", requested).strip()

    @staticmethod
    def _direct_target(value: str) -> str:
        requested = re.sub(
            r"^(?:kairon|cairon|kiron|kairom|cairo|caio|kyron)\s*",
            "",
            value.strip(" ,.!?"),
        )
        return re.sub(r"^(?:para\s+)?(?:o|a)\s+", "", requested).strip()

    @staticmethod
    def _target_command(target: ComputerTarget) -> ComputerCommand:
        return ComputerCommand(
            intent=StructuredIntent(action="open", target=target.label, risk=RiskLevel.SAFE),
            target=target,
        )

    @staticmethod
    def _blocked_command(target: str) -> ComputerCommand:
        return ComputerCommand(
            intent=StructuredIntent(
                action="blocked_system_action",
                target=target,
                risk=RiskLevel.CRITICAL,
            )
        )

    @staticmethod
    def _not_found_command(target: str) -> ComputerCommand:
        return ComputerCommand(
            intent=StructuredIntent(
                action="application_not_found",
                target=target,
                risk=RiskLevel.SAFE,
            )
        )

    @classmethod
    def _start_apps(cls) -> AppCatalog:
        if cls._cached_start_apps is not None:
            return cls._cached_start_apps
        command = (
            "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
            "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=True,
                capture_output=True,
                encoding="utf-8",
            )
            payload = json.loads(result.stdout or "[]")
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            logger.exception("computer_apps_index_failed")
            payload = []

        if isinstance(payload, dict):
            payload = [payload]
        cls._cached_start_apps = {
            normalize_text(str(item["Name"])): (str(item["Name"]), str(item["AppID"]))
            for item in payload
            if item.get("Name") and item.get("AppID")
        }
        return cls._cached_start_apps

    @staticmethod
    def _launch_process(command: tuple[str, ...]) -> None:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def _launch_start_app(app_id: str) -> None:
        subprocess.Popen(
            ("explorer.exe", f"shell:AppsFolder\\{app_id}"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _open_path(path: str) -> None:
        if not hasattr(os, "startfile"):
            raise OSError("Abertura de pastas esta disponivel apenas no Windows.")
        os.startfile(path)
