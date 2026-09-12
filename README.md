# Kairon

Assistente pessoal local para Windows, voice-first, com desktop em Tauri/React e core em Python/FastAPI.

## Status

Fundacao do MVP:

- Desktop: Tauri 2 + React + TypeScript + Vite.
- Core: FastAPI + WebSocket + SQLite.
- Voz: microfone real com Whisper local e voz neural brasileira.
- Interface: nucleo 3D reativo em Three.js com layout operacional responsivo.
- Wake word: deteccao local de "Kairon" via Whisper, separada da futura integracao Porcupine.
- TTS: voz neural masculina pt-BR-AntonioNeural, com fallback offline do Windows.
- Pesquisa: consulta automatica na web para pedidos explicitos e informacoes atuais, com fontes.
- Conhecimento: indexacao local de PDF, TXT e Markdown com recuperacao semantica e fontes.
- Computador: abre por voz aplicativos registrados no Menu Iniciar, pastas e sites permitidos.
- Midia: pesquisa e reproduz faixas no Spotify, pausa, continua, pula e controla o volume.
- Relogio: responde hora, data e dia da semana usando o horario local do Windows.
- Brain: `KaironCore`, roteador de intencoes e neuronios iniciais.
- Memoria: schema SQLite inicial.

Python e Rust precisam estar instalados para executar tudo localmente.

## Pre-requisitos

```powershell
node --version
pnpm --version
python --version
rustc --version
```

Instale o que faltar:

```powershell
winget install Python.Python.3.12
winget install Rustlang.Rustup
```

Depois feche e abra o terminal.

## Instalacao

```powershell
pnpm install
pnpm setup:python
```

## Execucao

Core:

```powershell
pnpm dev:core
```

Desktop web:

```powershell
pnpm --filter @kairon/desktop dev:web
```

App Tauri:

```powershell
pnpm dev
```

Use apenas um modo de desenvolvimento por vez. `pnpm dev` ja inicia o Vite na porta
1420; nao execute `pnpm dev:web` ao mesmo tempo. Se a porta ficar ocupada depois de
uma janela encerrada, feche o processo Vite antigo no Gerenciador de Tarefas e rode
`pnpm dev` novamente.

O desktop inicia e encerra o Kairon Core automaticamente. Para abrir sem uma janela de
terminal, execute `Kairon.vbs` por duplo clique.

Somente interface web, sem Python/Rust:

```powershell
pnpm dev:web
```

## Base de conhecimento

Coloque arquivos `.pdf`, `.txt` ou `.md` dentro da pasta `knowledge`. A Kairon detecta
arquivos novos, alterados ou removidos automaticamente antes da proxima pergunta e usa os
trechos relevantes na resposta.

Para forcar a recriacao completa do indice:

```powershell
pnpm knowledge:reindex
```

Tambem e possivel dizer: `Kairon, atualize a base de conhecimento`.

PDFs precisam conter texto selecionavel. Imagens digitalizadas ainda nao passam por OCR.

## Configuracao

Copie `.env.example` para `.env`.

### Companheiro compacto e conversa por voz (Ollama)

O mascote tem 148px, janela transparente de 320 x 560 e funciona somente por voz.
Arraste o mascote ou a barra **Kairon**; com foco neles, as setas tambem movem a janela.

O fluxo usa Ollama para a conversa e Whisper local para transcricao. A resposta usa voz neural Edge, com fallback local do Windows.

```dotenv
KAIRON_LLM_PROVIDER=ollama
```

Reinicie o Kairon e converse pelo microfone. A resposta chega em audio em frases curtas,
com deteccao de fim de fala e interrupcao quando voce fala novamente.

O Kairon roda localmente e nao envia o audio para provedores externos. O texto da resposta
segue para o Edge TTS quando a voz neural esta habilitada; o Windows assume como fallback.
Ollama continua sendo o unico provedor de LLM; pesquisa, memoria e comandos locais permanecem disponiveis.

- `KAIRON_LLM_PROVIDER=ollama`: conversa com IA local via Ollama.
- `KAIRON_OLLAMA_MODEL=qwen3:8b`: modelo local equilibrado para conversa e comandos em streaming.
- `KAIRON_OLLAMA_BASE_URL=http://127.0.0.1:11434`: API local do Ollama.
- `KAIRON_OLLAMA_FALLBACK_MODELS=`: modelos locais de reserva, separados por virgula.
- `KAIRON_OLLAMA_TIMEOUT_SECONDS=120`: limite por tentativa de modelo (tambem usado nos embeddings).
- `KAIRON_LLM_FAILURE_COOLDOWN_SECONDS=30`: pausa antes de tentar novamente um modelo que falhou.
- `KAIRON_DB_PATH=data/kairon.db`: banco SQLite local.
- `KAIRON_CONVERSATION_TIMEOUT_SECONDS=8`: tempo para manter modo conversa.
- `KAIRON_MICROPHONE_ECHO_GUARD_SECONDS=1.2`: bloqueio do microfone apos cada resposta.
- `KAIRON_STT_MODEL=base`: modelo Whisper local equilibrado para resposta rapida em CPU.
- `KAIRON_STT_LANGUAGE=pt`: idioma usado na transcricao.
- `KAIRON_STT_BEAM_SIZE=1`: prioriza baixa latencia na transcricao de voz.
- `KAIRON_MICROPHONE_DEVICE`: indice opcional do dispositivo de entrada.
- `KAIRON_MICROPHONE_VAD_MODE=1`: sensibilidade da deteccao de voz (0 mais sensivel, 3 menos).
- `KAIRON_MICROPHONE_SPEECH_FRAMES=3`: quantidade minima de quadros para iniciar a captura.
- `KAIRON_MICROPHONE_SILENCE_SECONDS=0.45`: pausa que encerra rapidamente uma frase.
- `KAIRON_MICROPHONE_MIN_RMS=20`: limite de volume do microfone para iniciar a transcricao.
- `KAIRON_WAKE_WORD_MODEL=models/wake-word/kairon.ppn`: futuro modelo Porcupine.
- `KAIRON_WAKE_WORD_REQUIRED=true`: exige dizer "Kairon" antes de aceitar um comando.
- `KAIRON_TTS_PROVIDER=edge`: voz neural natural pela internet; usa Windows como fallback.
- `KAIRON_WEB_SEARCH_MAX_RESULTS=5`: quantidade maxima de fontes por pesquisa.
- `KAIRON_KNOWLEDGE_PATH=knowledge`: pasta monitorada para documentos locais.
- `KAIRON_KNOWLEDGE_EMBEDDING_MODEL=nomic-embed-text-v2-moe`: embeddings multilingues locais.
- `KAIRON_TTS_VOICE=pt-BR-AntonioNeural`: voz masculina em português.
- `KAIRON_TTS_PITCH=+0Hz`: tonalidade natural da voz neural.

## Arquitetura

```text
apps/desktop      Interface Tauri/React
core/brain        KaironCore, contexto e roteamento
core/knowledge    Leitura, fragmentacao, embeddings e recuperacao documental
core/neurons      Neuronios modulares
core/voice        Wake word, STT, TTS e audio manager
core/memory       SQLite e repositorios
core/websocket    Canal realtime com o frontend
data/             Banco local
knowledge/        PDFs, textos e Markdown fornecidos pelo usuario
models/wake-word  Modelo kairon.ppn futuramente
```

## Voz e Wake Word

No modo Local, **Ligar microfone** inicia a escuta do microfone padrao. Por seguranca, somente
frases que comecam com "Kairon" viram pedidos. O audio permanece em memoria.

Na primeira instalacao, `pnpm setup:python` baixa o modelo configurado. O futuro provider
Porcupine implementara a mesma interface e carregara:

```text
models/wake-word/kairon.ppn
```

## Troca de Providers

As interfaces estao em:

- Wake word: `core/voice/wake_word/base.py`
- STT: `core/voice/stt/base.py`
- TTS: `core/voice/tts/base.py`
- LLM: `core/providers/llm/base.py`

## Troubleshooting

### Modelos de reserva e diagnostico

Se um modelo falhar, exceder o tempo limite ou retornar uma resposta invalida, o Kairon tenta
o proximo modelo configurado, preservando historico, memorias, pesquisa e documentos.
Modelos que falharam ficam em pausa pelo cooldown; depois, o principal volta a ter prioridade.
Se todos falharem ou estiverem em pausa, o erro e informado sem simular uma resposta.

No `.env`, configure somente modelos de conversa que voce ja instalou no Ollama:

```dotenv
KAIRON_OLLAMA_MODEL=llama3.2:3b
# Exemplo: use apenas se esse modelo tambem estiver instalado.
KAIRON_OLLAMA_FALLBACK_MODELS=llama3.1:latest
KAIRON_OLLAMA_TIMEOUT_SECONDS=120
KAIRON_LLM_FAILURE_COOLDOWN_SECONDS=30
```

A lista de reservas fica vazia por padrao. Nao ha download automatico nem envio para provedores
externos. Todos os modelos usam o mesmo Ollama; a reserva nao resolve o servidor estar offline.
O limite e por modelo: duas tentativas de 120 segundos podem somar 240 segundos de geracao.
A recuperacao documental e a pesquisa ocorrem separadamente desse limite.

Consulte `GET http://127.0.0.1:8765/llm/status` para ver o ultimo modelo que respondeu,
o ultimo erro e o tempo ate a proxima tentativa. O estado e baseado nas chamadas anteriores:
`unknown` (sem sucesso confirmado apos a ultima falha), `ready` (ultima chamada bem-sucedida)
ou `cooldown` (em pausa). Essa consulta nao testa a disponibilidade atual nem chama a IA.

Inspiracao: cadeia de provedores do [Jarvis de Venkata Mannem](https://github.com/ONEPUNCHMAN411/Jarvis),
reimplementada usando os contratos e dependencias existentes do Kairon.

### Problemas comuns

- `python` nao encontrado: instale Python pelo `winget` e reabra o terminal.
- `rustc` nao encontrado: instale Rustup pelo `winget`, execute `rustup default stable` e reabra o terminal.
- `.venv` nao encontrado: rode `pnpm setup:python`.
- Ollama offline: abra o Ollama e confirme com `ollama list`.
- Modelo ausente: execute `ollama pull llama3.2:3b`.
- Embeddings ausentes: execute `ollama pull nomic-embed-text-v2-moe`.
- WebSocket desconectado: inicie `pnpm dev:core` e confirme porta `8765`.
- Microfone indisponivel: permita acesso ao microfone nas Configuracoes de Privacidade do Windows.
- Microfone incorreto: liste dispositivos com `python -m sounddevice` e configure `KAIRON_MICROPHONE_DEVICE`.
- Voz nao detectada: confirme o dispositivo padrao ou configure `KAIRON_MICROPHONE_DEVICE`.
- Voz neural indisponivel: o Kairon usa automaticamente a voz nativa do Windows.
