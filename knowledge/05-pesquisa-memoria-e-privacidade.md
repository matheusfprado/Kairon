# Pesquisa, memoria e privacidade

## Pesquisa na internet

Kairon pesquisa automaticamente quando a pergunta depende de informacao atual, como
noticias, clima, cotacoes, precos, placares, eleicoes ou lancamentos. Tambem pesquisa quando
o usuario pede explicitamente usando verbos como pesquisar, buscar, procurar ou consultar.

A pesquisa retorna ate cinco resultados. Os resumos encontrados sao enviados ao modelo e
os links aparecem como fontes consultadas na interface. Kairon nao deve falar URLs em voz
alta. Uma afirmacao comum que apenas menciona internet nao dispara pesquisa automaticamente.

## Memoria

As mensagens recentes ficam associadas a uma conversa no SQLite. Memorias importantes
podem ser armazenadas separadamente por tipo, incluindo projeto, preferencia e fato. A
memoria serve para personalizar conversas futuras; a base documental serve para consultar
conteudo fornecido pelo usuario.

## Privacidade

O Ollama, o Whisper, os embeddings, o SQLite e a recuperacao documental rodam localmente.
Consultas de pesquisa web e a voz Edge neural dependem de servicos externos. Para voz
totalmente offline, o provider de TTS pode ser alterado para `windows`, com qualidade menor.

Documentos privados nao devem ser enviados para a pesquisa web. Eles sao usados como
contexto local do modelo. A base deve conter apenas arquivos que o usuario esta autorizado
a armazenar e consultar.
