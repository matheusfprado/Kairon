# Comandos e operacao

## Inicializacao

- `pnpm dev`: abre o desktop Tauri, inicia o Ollama quando necessario e inicia o core Python.
- `Kairon.vbs`: abre o mesmo desktop com os terminais ocultos.
- `pnpm dev:core`: inicia somente o FastAPI na porta 8765.
- `pnpm dev:web`: abre somente a interface web na porta 1420.
- `pnpm setup:python`: cria o ambiente Python, instala dependencias e baixa os modelos.

## Base de conhecimento

- `pnpm knowledge:index`: sincroniza somente documentos alterados.
- `pnpm knowledge:reindex`: recria os embeddings de todos os documentos.
- `GET /knowledge/status`: retorna quantidade de documentos e trechos indexados.
- `POST /knowledge/reindex`: solicita reindexacao completa pela API local.

## Qualidade e diagnostico

- `pnpm test`: executa os testes Python.
- `pnpm lint`: executa o lint do desktop.
- `pnpm typecheck`: verifica os tipos TypeScript.
- `pnpm build`: gera o build de producao do frontend.
- `ollama list`: mostra os modelos instalados.
- `ollama ps`: mostra os modelos carregados na memoria.

As configuracoes locais usam variaveis com prefixo `KAIRON_` e podem ser definidas no
arquivo `.env`. O arquivo `.env.example` documenta os valores disponiveis.
