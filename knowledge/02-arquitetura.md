# Arquitetura da Kairon

## Desktop

A interface fica em `apps/desktop` e usa Tauri 2, React 19, TypeScript, Vite, Zustand,
Lucide e Three.js. A cena tridimensional e carregada de forma assincrona para reduzir o
tamanho do pacote inicial. O Tauri inicia o processo Python automaticamente e encerra esse
processo quando a janela desktop e fechada.

## Core

O nucleo fica em `core` e expoe um servidor FastAPI em `127.0.0.1:8765`. O desktop se
comunica com ele pelo WebSocket `/ws`. O endpoint `/health` indica disponibilidade do core.

`KaironCore` registra a mensagem, recupera memorias e documentos relevantes, pede ao
`IntentRouter` que escolha um neuronio e grava a resposta. Os neuronios atuais cuidam de
conversa, memoria, status do sistema, pesquisa web e gerenciamento da base documental.

## Providers

O modelo de linguagem usa a API local do Ollama. A transcricao usa Faster Whisper. A voz
principal usa Edge TTS e pode recorrer ao sintetizador SAPI do Windows. A busca web usa um
provider separado, mantendo a regra de negocio independente do mecanismo de pesquisa.

## Persistencia

O banco `data/kairon.db` e SQLite. Ele guarda conversas, mensagens, memorias, documentos,
fragmentos e embeddings. O conteudo original dos documentos permanece na pasta `knowledge`.
