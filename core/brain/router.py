from core.brain.context import KaironContext
from core.neurons.base import Neuron


class IntentRouter:
    def __init__(self, neurons: list[Neuron]) -> None:
        self.neurons = neurons

    async def route(self, context: KaironContext) -> Neuron:
        scored: list[tuple[float, Neuron]] = []
        for neuron in self.neurons:
            scored.append((await neuron.can_handle(context), neuron))
        return max(scored, key=lambda item: item[0])[1]
