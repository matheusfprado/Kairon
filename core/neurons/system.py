import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import ClassVar

from core.brain.context import KaironContext
from core.memory.extractor import normalize_text
from core.neurons.base import Neuron, NeuronResult
from core.security.permissions import RiskLevel
from core.system.computer import ComputerController
from core.system.media import SpotifyControlError, SpotifyController

logger = logging.getLogger("SYSTEM")

WEEKDAYS = (
    "segunda-feira",
    "ter\u00e7a-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "s\u00e1bado",
    "domingo",
)
MONTHS = (
    "janeiro",
    "fevereiro",
    "mar\u00e7o",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
TIME_PATTERN = re.compile(
    r"\b(?:que horas(?: sao)?|qual (?:e )?(?:a hora|o horario)(?: atual)?|"
    r"me (?:diga|fale) (?:a hora|as horas))"
    r"(?: agora| hoje)?(?=\s*(?:[?.!]|$|e (?:que|qual) dia))"
)
DATE_PATTERN = re.compile(
    r"\b(?:(?:que|qual) (?:e o )?dia(?: da semana)?(?: e)?(?: hoje)?|"
    r"(?:qual (?:e )?a )?data(?: de hoje)?|dia de hoje)(?=\s*(?:[?.!]|$))"
)


class SystemNeuron(Neuron):
    name = "system"
    description = "Status local e comandos seguros do sistema"
    capabilities: ClassVar[list[str]] = [
        "status",
        "time",
        "open_apps",
        "open_folders",
        "open_sites",
    ]

    def __init__(
        self,
        controller: ComputerController | None = None,
        media_controller: SpotifyController | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.controller = controller or ComputerController()
        self.media_controller = media_controller or SpotifyController()
        self.clock = clock or (lambda: datetime.now().astimezone())

    async def can_handle(self, context: KaironContext) -> float:
        normalized = normalize_text(context.user_input)
        if self.media_controller.parse(context.user_input) is not None:
            return 0.995
        if self._requests_time(normalized) or self._requests_date(normalized):
            return 0.99
        if self.controller.parse(context.user_input) is not None:
            return 0.98
        if "status" in normalized or "acesso ao computador" in normalized:
            return 0.8
        return 0.1

    async def execute(
        self, context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        normalized = normalize_text(context.user_input)
        media_command = self.media_controller.parse(context.user_input)
        if media_command is not None:
            try:
                response = await asyncio.to_thread(self.media_controller.execute, media_command)
            except SpotifyControlError as exc:
                logger.warning("media_action_failed action=%s error=%s", media_command.action, exc)
                return NeuronResult(response=f"Nao consegui controlar o Spotify: {exc}")
            logger.info("media_action_executed action=%s", media_command.action)
            return NeuronResult(response=response)

        wants_time = self._requests_time(normalized)
        wants_date = self._requests_date(normalized)
        if wants_time or wants_date:
            return NeuronResult(response=self._date_time_response(wants_time, wants_date))

        command = self.controller.parse(context.user_input)
        if command is None:
            return NeuronResult(
                response=(
                    f"O nucleo esta ativo. Encontrei {self.controller.available_app_count} "
                    "aplicativos e posso abri-los por nome, alem de pastas e sites."
                )
            )

        if command.intent.risk != RiskLevel.SAFE:
            return NeuronResult(
                response=(
                    "Nao executei essa acao porque ela pode alterar ou desligar o computador. "
                    "Comandos sensiveis permanecem bloqueados."
                )
            )

        if command.intent.action == "application_not_found":
            return NeuronResult(
                response=f"Nao encontrei um aplicativo chamado {command.intent.target}."
            )

        try:
            label = await asyncio.to_thread(self.controller.execute, command)
        except (OSError, PermissionError) as exc:
            logger.warning("computer_action_failed target=%s error=%s", command.intent.target, exc)
            return NeuronResult(response=f"Nao consegui abrir {command.intent.target}: {exc}")

        logger.info("computer_action_executed target=%s", label)
        return NeuronResult(response=f"Abrindo {label}.")

    def _date_time_response(self, wants_time: bool, wants_date: bool) -> str:
        now = self.clock()
        responses: list[str] = []
        if wants_time:
            if now.minute == 0:
                responses.append(f"Agora s\u00e3o {now.hour} horas em ponto")
            else:
                responses.append(f"Agora s\u00e3o {now.hour} horas e {now.minute} minutos")
        if wants_date:
            responses.append(
                f"hoje \u00e9 {WEEKDAYS[now.weekday()]}, {now.day} de "
                f"{MONTHS[now.month - 1]} de {now.year}"
            )
        return ". ".join(responses) + "."

    @staticmethod
    def _requests_time(normalized: str) -> bool:
        return TIME_PATTERN.search(normalized) is not None

    @staticmethod
    def _requests_date(normalized: str) -> bool:
        return DATE_PATTERN.search(normalized) is not None
