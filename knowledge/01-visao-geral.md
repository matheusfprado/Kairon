# Visao geral da Kairon

Kairon e uma assistente pessoal de voz executada localmente no Windows. Seu objetivo e
permitir uma conversa natural por microfone, responder em voz alta, consultar informacoes
atuais na internet e usar documentos privados como contexto.

O desktop e uma aplicacao Tauri 2 com React, TypeScript, Vite e uma cena Three.js reativa.
O nucleo usa Python 3.12, FastAPI, WebSocket e SQLite. A conversa local e gerada pelo Ollama
com o modelo `llama3.2:3b`.

## Capacidades atuais

- Reconhecimento de fala em portugues brasileiro com Faster Whisper.
- Deteccao local da palavra de ativacao Kairon.
- Conversa com contexto recente e memorias armazenadas em SQLite.
- Resposta falada com voz neural brasileira e fallback nativo do Windows.
- Pesquisa de noticias, clima, precos e outros assuntos atuais na internet.
- Base documental local para PDF, TXT e Markdown.
- Interface visual futurista que reage aos estados de escuta, processamento e fala.

Kairon nao precisa ser treinada novamente para receber documentos. Ela usa recuperacao
semantica: encontra trechos relevantes na base e os entrega ao modelo no momento da resposta.
