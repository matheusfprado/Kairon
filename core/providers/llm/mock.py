from core.brain.context import KaironContext
from core.providers.llm.base import LlmProvider


class MockLlmProvider(LlmProvider):
    async def complete(self, context: KaironContext) -> str:
        normalized = context.user_input.lower()

        if "seu nome" in normalized or "qual e o seu nome" in normalized or "qual é o seu nome" in normalized:
            return "Meu nome é Kairon."

        if "acabei de perguntar" in normalized:
            previous_user_messages = [
                message["content"]
                for message in context.recent_messages
                if message["role"] == "user" and message["content"] != context.user_input
            ]
            if previous_user_messages:
                return f"Você acabou de perguntar: {previous_user_messages[-1]}"
            return "Ainda não tenho uma pergunta anterior nesta conversa."

        if "luma" in normalized:
            return "Vou lembrar que você está trabalhando no Luma."

        return "A conversa com IA ainda não está configurada."
