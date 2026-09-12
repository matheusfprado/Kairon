# Solucao de problemas

## O aplicativo nao abre

Execute `pnpm check:env`. Python 3.12, Rust/Cargo, Node, pnpm e Ollama precisam estar
disponiveis. Se `.venv` estiver ausente, execute `pnpm setup:python`. Se o Cargo estiver
instalado mas nao for reconhecido, reabra o PowerShell para atualizar o PATH.

## Ollama ou inteligencia artificial indisponivel

Confirme com `ollama list`. O modelo de conversa esperado e `llama3.2:3b`. O modelo da base
documental e `nomic-embed-text-v2-moe`. Para instala-los, use `ollama pull` seguido do nome.

## Core desconectado

Verifique `http://127.0.0.1:8765/health`. O desktop tenta se reconectar automaticamente.
Outro processo usando a porta 8765 pode impedir a inicializacao.

## Microfone nao reconhece corretamente

Permita o microfone nas configuracoes de privacidade do Windows. Confira o dispositivo
padrao ou execute `python -m sounddevice` e configure `KAIRON_MICROPHONE_DEVICE`. Reduza o
ruido ambiente e fale depois de ouvir "Estou ouvindo".

## A assistente escuta a propria resposta

Use fones de ouvido ou reduza o volume dos alto-falantes. Kairon ja bloqueia o microfone
durante a fala, aplica uma guarda depois da resposta e descarta transcricoes parecidas com a
ultima resposta. O tempo extra pode ser ajustado em `KAIRON_MICROPHONE_ECHO_GUARD_SECONDS`.

## Documento nao aparece nas respostas

Confirme que ele esta em `knowledge` e tem extensao PDF, TXT ou Markdown. Rode
`pnpm knowledge:reindex`. PDFs escaneados como imagem precisam primeiro de OCR. Consulte
`http://127.0.0.1:8765/knowledge/status` para verificar documentos e trechos indexados.
