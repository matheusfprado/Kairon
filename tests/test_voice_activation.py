import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.websocket.events import KaironState, StateChangedEvent
from core.websocket.server import KaironWebSocketSession


def make_session(command: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        send=AsyncMock(),
        speak=AsyncMock(),
        process_text=AsyncMock(),
        listen_for_command=AsyncMock(return_value=command),
        conversation_timeout_seconds=8,
        _stop_event=threading.Event(),
    )


@pytest.mark.asyncio
async def test_wake_word_allows_exactly_one_follow_up_command() -> None:
    session = make_session("pesquise noticias de hoje")

    await KaironWebSocketSession.handle_wake_word(session, None)

    session.listen_for_command.assert_awaited_once_with(8)
    session.speak.assert_not_awaited()
    session.process_text.assert_awaited_once_with("pesquise noticias de hoje")
    assert session.send.await_args_list[-1].args == (
        StateChangedEvent(state=KaironState.LISTENING_FOR_WAKE_WORD),
    )


@pytest.mark.asyncio
async def test_inline_wake_command_does_not_open_continuous_listening() -> None:
    session = make_session("comando que nao deve ser capturado")

    await KaironWebSocketSession.handle_wake_word(session, "abra o Spotify")

    session.listen_for_command.assert_not_awaited()
    session.speak.assert_not_awaited()
    session.process_text.assert_awaited_once_with("abra o Spotify")
