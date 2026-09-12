# Voz, microfone e conversa

Kairon usa o microfone padrao do Windows. Para iniciar uma conversa, o usuario fala
"Kairon". Variacoes foneticas comuns tambem sao aceitas. Depois da ativacao, a assistente
diz "Estou ouvindo", captura a pergunta, transcreve, responde e continua escutando por
alguns segundos para permitir novas perguntas sem repetir a palavra de ativacao.

## Reconhecimento de fala

O modelo padrao de transcricao e Whisper `small`, configurado para portugues. O audio e
capturado em memoria e nao e salvo como arquivo. Um detector de atividade vocal identifica
o inicio e o fim de cada frase.

## Resposta falada

A voz neural padrao e `pt-BR-AntonioNeural`, com velocidade `-5%` e pitch `-12Hz`. O audio
e reproduzido em streaming para comecar antes que toda a fala seja baixada. Se a voz neural
falhar, Kairon usa a voz nativa do Windows.

## Protecao contra eco

Enquanto Kairon fala, o gravador e suprimido. Depois da resposta existe uma guarda curta de
eco. A transcricao tambem e comparada com a ultima resposta falada; frases muito parecidas
sao descartadas para impedir que Kairon interprete a propria voz como uma nova pergunta.

Se o microfone incorreto estiver ativo, execute `python -m sounddevice` e configure o indice
em `KAIRON_MICROPHONE_DEVICE`. O acesso ao microfone deve estar permitido nas configuracoes
de privacidade do Windows.
