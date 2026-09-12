from core.websocket.server import is_likely_echo


def test_rejects_same_assistant_response() -> None:
    spoken = "Meu nome é Kairon. Como posso ajudar você?"

    assert is_likely_echo("Meu nome é Kairon, como posso ajudar você", spoken)


def test_rejects_partial_assistant_response() -> None:
    spoken = "Posso conversar com você e responder perguntas de forma natural."

    assert is_likely_echo("conversar com você e responder perguntas", spoken)


def test_accepts_new_user_question() -> None:
    spoken = "Meu nome é Kairon."

    assert not is_likely_echo("Qual é a capital do Brasil?", spoken)
