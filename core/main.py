import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from core.brain.core import KaironCore
from core.brain.router import IntentRouter
from core.config import get_settings
from core.knowledge.embeddings import OllamaEmbeddingProvider
from core.knowledge.loader import DocumentChunker, DocumentLoader
from core.knowledge.repository import KnowledgeRepository
from core.knowledge.service import KnowledgeBase
from core.logging_config import configure_logging
from core.memory.database import Database
from core.memory.repository import MemoryRepository
from core.neurons.conversation import ConversationNeuron
from core.neurons.knowledge import KnowledgeNeuron
from core.neurons.memory import MemoryNeuron
from core.neurons.system import SystemNeuron
from core.neurons.web_research import WebResearchNeuron
from core.providers.llm.factory import create_llm
from core.providers.llm.router import LlmStatus
from core.providers.search.web import WebSearchProvider
from core.voice.microphone import MicrophoneRecorder
from core.voice.stt.faster_whisper import FasterWhisperSpeechToTextProvider
from core.voice.tts.edge import EdgeNeuralTextToSpeechProvider
from core.voice.tts.windows import WindowsTextToSpeechProvider
from core.voice.wake_word.whisper import WhisperWakeWordProvider
from core.websocket.server import KaironWebSocketSession

configure_logging()

settings = get_settings()
database = Database(settings.db_path)
database.initialize()
connection = database.connect()
memory_repository = MemoryRepository(connection)
knowledge_base = KnowledgeBase(
    root=Path(settings.knowledge_path),
    repository=KnowledgeRepository(connection),
    embeddings=OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.knowledge_embedding_model,
        dimensions=settings.knowledge_embedding_dimensions,
        timeout_seconds=settings.ollama_timeout_seconds,
    ),
    loader=DocumentLoader(max_file_bytes=settings.knowledge_max_file_mb * 1_048_576),
    chunker=DocumentChunker(),
    search_limit=settings.knowledge_search_limit,
    min_score=settings.knowledge_min_score,
)
llm = create_llm(settings)
router = IntentRouter(
    neurons=[
        MemoryNeuron(),
        KnowledgeNeuron(knowledge_base),
        SystemNeuron(),
        WebResearchNeuron(
            llm=llm,
            search=WebSearchProvider(max_results=settings.web_search_max_results),
        ),
        ConversationNeuron(llm),
    ]
)
kairon_core = KaironCore(
    router=router,
    memory_repository=memory_repository,
    knowledge_base=knowledge_base,
)
windows_tts = WindowsTextToSpeechProvider()
tts = (
    EdgeNeuralTextToSpeechProvider(
        voice=settings.tts_voice,
        rate=settings.tts_rate,
        pitch=settings.tts_pitch,
        fallback=windows_tts,
        output_device=settings.audio_output_device,
    )
    if settings.tts_provider == "edge"
    else windows_tts
)
stt = FasterWhisperSpeechToTextProvider(
    model_name=settings.stt_model,
    language=settings.stt_language,
    beam_size=settings.stt_beam_size,
)
recorder = MicrophoneRecorder(
    device=settings.microphone_device,
    vad_mode=settings.microphone_vad_mode,
    speech_frames=settings.microphone_speech_frames,
    silence_seconds=settings.microphone_silence_seconds,
    min_rms=settings.microphone_min_rms,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.gather(llm.prepare(), stt.prepare())
    if settings.llm_provider == "ollama":
        await knowledge_base.sync()
    yield


app = FastAPI(title="Kairon Core", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1420", "http://localhost:1420", "tauri://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/knowledge/status")
async def knowledge_status() -> dict[str, int]:
    return knowledge_base.status().model_dump()


@app.get("/llm/status")
async def llm_status() -> LlmStatus:
    return llm.status()


@app.get("/memory/status")
async def memory_status() -> dict[str, int]:
    return {"count": kairon_core.memory_count()}


@app.post("/knowledge/reindex")
async def knowledge_reindex() -> dict[str, int]:
    return (await knowledge_base.sync(force=True)).model_dump()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, voice: bool = True) -> None:
    session = KaironWebSocketSession(
        websocket=websocket,
        core=kairon_core,
        recorder=recorder,
        stt=stt,
        tts=tts,
        wake_word=WhisperWakeWordProvider(
            recorder=recorder,
            stt=stt,
            aliases=settings.wake_word_aliases,
            required=settings.wake_word_required,
        ),
        conversation_timeout_seconds=settings.conversation_timeout_seconds,
        echo_guard_seconds=settings.microphone_echo_guard_seconds,
        voice_enabled=voice,
    )
    await session.run()
