# Base de conhecimento e memoria

A base documental e diferente da memoria de conversa. Memorias representam fatos e
preferencias aprendidos durante o uso. A base de conhecimento representa documentos que o
usuario forneceu deliberadamente.

## Como adicionar conhecimento

Coloque arquivos PDF, TXT ou Markdown dentro da pasta `knowledge`. Subpastas tambem sao
aceitas. Antes da proxima pergunta, Kairon detecta documentos novos, alterados ou removidos.
Somente arquivos modificados sao reprocessados.

O limite padrao e 25 MB por arquivo. PDFs precisam conter texto selecionavel; documentos
digitalizados apenas como imagem ainda nao passam por OCR.

## Como funciona a consulta

Cada documento e dividido em trechos com pequena sobreposicao. O modelo local
`nomic-embed-text-v2-moe` gera embeddings multilingues de 256 dimensoes. Na pergunta,
Kairon cria um embedding da consulta, calcula similaridade de cosseno e seleciona ate quatro
trechos acima do limite de relevancia. O Ollama recebe somente esses trechos para redigir a
resposta.

As fontes locais aparecem na interface com o nome do documento e, para PDFs, o numero da
pagina. Instrucoes encontradas dentro dos documentos sao tratadas apenas como dados e nao
substituem as regras do sistema.

Para reconstruir tudo, execute `pnpm knowledge:reindex` ou diga "Kairon, atualize a base de
conhecimento". Para saber o tamanho da base, pergunte "quantos documentos existem na base?".
