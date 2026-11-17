# Manual de produção — TikTok de dicas de Valorant e Fortnite (console)

Este manual é seguido pelas tarefas agendadas, que produzem os vídeos sozinhas e entregam ao dono, que posta à mão no TikTok.
Cada execução produz **um** episódio:

| Execução (horário de São Paulo) | Vai ao ar | Jogo |
| --- | --- | --- |
| tarefa das 13h55 | 14:00 (ou ~14:10) | **Fortnite** |
| tarefa das 16h23 | 19:00 | **Valorant** |

## Fluxo de cada execução

1. Ler este manual, `fabrica/aprendizados.md`, `fabrica/historico.md`, `fabrica/pautas.md` e `gameplay/catalogo.json`.
2. Se não houver clipes do jogo do horário no catálogo: **não produza nada**, avise por notificação e encerre.
3. Pesquisar na web o que mudou recentemente no jogo (patch do Valorant, temporada/atualização do Fortnite) antes de falar de
   armas, meta ou números. Na dúvida sobre um dado, não use o dado.
4. Escolher o tema (regras abaixo), escolher os clipes no catálogo e escrever o `episodio.json`.
5. Commit + push na `main`. O GitHub Actions narra (voz grátis pt-BR-AntonioNeural) e monta o vídeo
   (`episodios/<pasta>/video.mp4`, `status.json` e `videos/<pasta>.mp4`).
6. Conferir o vídeo (mosaico de quadros). No máximo uma correção.
7. Entregar o vídeo e o texto do post ao dono (seção "Entrega"). Atualizar `historico.md` e o campo `usos` dos clipes usados no `catalogo.json`. Commit + push.

## Público e linha editorial

- Jogadores de **console** (PS5/Xbox, controle). Fale de controle, configurações de console e situações de quem joga no controle.
- Temas: **posicionamento**, **armas e loadout**, **mapas e spots**, **curiosidades/easter eggs**, **configurações de controle**,
  **erros comuns**, **dicas de ranked**, **meta da temporada/patch**, **utilitários e agentes** (Valorant), **build e zero build** (Fortnite).
- Tom: parceiro que joga bem, direto, empolgado sem exagero, gíria leve de gamer BR ("bota", "rushar", "clutch", "peek").
  Sem palavrão, sem ofensa a outros jogadores.
- Proibido: ensinar trapaça, bug abuse que dá ban, macro, Cronus/XIM ou qualquer coisa contra as regras do jogo;
  prometer "subir de elo garantido"; usar marca, logo ou personagem de terceiros fora do próprio jogo.

## O que faz vídeo de games viralizar (aplique em todo roteiro)

- **30 a 45 segundos** (roteiro de **450 a 600 caracteres**). Vídeos curtos dominam entre os virais.
- **Gancho nos primeiros 3 segundos**: comece pelo resultado, pelo número ou pela dor. Exemplos:
  "Pare de fazer isso no Ascent", "3 erros que te fazem perder o round", "A arma mais roubada da temporada",
  "Ninguém te contou isso sobre o controle". **Nunca** comece com "Olá, pessoal" ou contexto longo.
- O primeiro clipe precisa ser o **momento mais forte** (abate, clutch, vitória) e o `titulo_tela` precisa dizer a promessa do vídeo.
- Formato de lista ("3 dicas", "2 erros") ou de comparação ("X ou Y?") prende mais. Uma ideia por cena.
- Use a bolha `pergunta` como gancho em alguns vídeos (dúvida comum de jogador), sem inventar nome de usuário.
- Termine com uma **pergunta para comentar** ("qual arma você usa?") ou "segue pra parte 2". Comentário puxa alcance.
- Legenda queimada palavra por palavra já é feita pela fábrica.
- Hashtags: **8 a 10**, misturando do jogo, de console e genéricas. Exemplos:
  Valorant: `valorant valorantconsole valorantbrasil dicasvalorant valorantclips ps5 gaming fyp foryou`
  Fortnite: `fortnite fortnitebrasil dicasfortnite fortniteps5 fortniteclips zerobuild gaming fyp foryou`

## Escolha do tema

- Não repita tema publicado nos últimos 30 dias (veja `historico.md`). Séries ("parte 2") podem continuar.
- Siga o que `aprendizados.md` diz que performa melhor.
- O tema precisa combinar com os clipes disponíveis. Se a dica é sobre um mapa/arma, use clipes desse mapa/arma.
  Se não houver, escolha outro tema ou use dica geral com clipes genéricos — **nunca** aponte com `marcador` para algo que o clipe não mostra.
- Alterne os tipos de tema ao longo da semana (posicionamento, arma, mapa, curiosidade, configuração, erro comum).

## Escolha dos clipes (`gameplay/catalogo.json`)

```json
{
  "clipes": [
    {
      "arquivo": "gameplay/valorant/v_partida1_003.mp4",
      "jogo": "valorant",
      "duracao": 30.0,
      "mapa": "Ascent",
      "personagem": "Jett",
      "armas": ["Vandal"],
      "resumo": "Defesa no B, segura o main com Vandal e faz 2 abates",
      "momentos": [{"t": 12.4, "o_que": "abate na cabeça segurando o main do B", "forca": 4}],
      "usos": 0,
      "ultimo_uso": ""
    }
  ]
}
```

- `forca` vai de 1 a 5 (5 = momento mais impressionante). Use os de força alta no começo do vídeo.
- Em cada cena, `de` é o segundo do clipe onde a cena começa. Comece 0,5 a 1 s antes do momento.
- Prefira clipes com menos `usos` e sem uso nos últimos 7 dias. Depois de entregar, some 1 em `usos` e preencha `ultimo_uso`.
- **Pode repetir clipes** (decisão do dono): quando os clipes novos acabarem, reutilize os de menor `usos`,
  de preferência outro trecho (`de`) ou outro `zoom`, para não ficar idêntico a um vídeo anterior.
- Varie: não use o mesmo trecho em duas cenas do mesmo vídeo.
- `plataforma`: "pc" ou "console". Clipes de PC servem para dicas gerais (posicionamento, mapa, economia, utilitário,
  curiosidade). **Não use clipe de PC em dica específica de controle/configuração de console**, porque engana quem assiste.
- `qualidade`: "1080p" ou "480p". Clipes 480p ficam borrados com zoom alto: use `zoom` entre 1.0 e 1.15 neles.
- `audio_ok`: se for false, use `"mudo": true` nas cenas com esse clipe.
- **Sem crédito** (decisão do dono, a pedido de quem cedeu a gameplay): não preencha `credito` no `episodio.json` e não
  escreva nada sobre origem da gameplay (nomes, @, "cedida por amigos") no vídeo, na legenda ou nas hashtags.
- `evitar`: trecho do clipe que não pode aparecer (placar, transição). Escolha `de` para a cena não passar por ele.
- `momentos` foram detectados pelo som (picos de tiro). Antes de apontar algo com `marcador`, confira o quadro no clipe;
  se não der para conferir, não use `marcador` naquela cena.

## Estilo visual: minimalista (decisão do dono)

O vídeo é só: fundo com a própria jogada desfocada e escurecida, gameplay grande no meio, título curto em texto branco simples acima e legenda discreta
(2 a 3 palavras por vez) abaixo. **Sem elementos** (balões, selos, números, marcadores, cards), sem efeitos sonoros e sem
nada que pareça edição feita por IA. Não preencha `elementos` nas cenas. Zoom: Valorant 1.7, Fortnite 1.35 (clipes 480p).
O estilo antigo com elementos só é usado se o `episodio.json` tiver `"estilo": "cards"`, e não deve ser usado.

## Formato do `episodio.json`

```json
{
  "jogo": "valorant",
  "titulo": "Título do post no TikTok (até 60 caracteres)",
  "titulo_tela": "3 ERROS QUE TE FAZEM PERDER O ROUND",
  "roteiro": "Texto completo da narração...",
  "legenda": "Legenda do post: 1 frase + pergunta para comentar.",
  "hashtags": ["valorant", "valorantconsole", "..."],
  "volume_jogo": 0.22,
  "cenas": [
    {"inicio": "", "clipe": "gameplay/valorant/v_partida1_003.mp4", "de": 11.5, "zoom": 1.35,
     "elementos": [{"tipo": "pergunta", "texto": "Por que eu sempre morro primeiro?"}]},
    {"inicio": "Primeiro", "clipe": "gameplay/valorant/v_partida1_007.mp4", "de": 3, "zoom": 1.5, "foco_x": 0.5,
     "elementos": [{"tipo": "numero", "texto": "1"}, {"tipo": "marcador", "x": 0.62, "y": 0.45, "texto": "fica aqui", "aos": 0.4}]}
  ]
}
```

- `titulo_tela`: frase curta (até ~40 caracteres) que fica fixa no topo o vídeo todo. É a promessa do vídeo.
- Uma cena nova a cada **2 a 4 segundos** (8 a 14 cenas). A primeira tem `"inicio": ""`.
- `inicio`: palavra exata do roteiro onde a cena começa (sem pontuação). As palavras têm que aparecer **na ordem** do roteiro.
- `zoom`: 1.0 mostra a tela inteira; 1.35 (padrão) aproxima; até 2.0 para destacar a mira ou um detalhe.
  `foco_x`: 0 a 1, para onde o recorte puxa na horizontal (0.5 = centro, onde fica a mira).
- `volume_jogo`: volume do som original da gameplay (0.15 a 0.3).

### Elementos (até 3 por cena; não repita o mesmo tipo em cenas seguidas)

| tipo | campos | onde aparece | uso |
| --- | --- | --- | --- |
| `numero` | `texto` | canto do gameplay | marcar a dica 1, 2, 3 |
| `marcador` | `x`, `y` (0 a 1 no gameplay), `texto`?, `aos`? (s) | sobre o gameplay | apontar posição, ângulo, spot |
| `pergunta` | `texto`, `rotulo`? | faixa de baixo | gancho com dúvida comum |
| `texto` | `texto`, `cor`?, `cor_texto`? | faixa de baixo | frase de apoio |
| `lista` | `itens` (até 4), `marcar` ("check" ou "x") | faixa de baixo | checklist |
| `versus` | `a`, `b`, `cor_a`?, `cor_b`? | faixa de baixo | comparação de armas/agentes |
| `riscado` | `texto` | faixa de baixo | erro comum |
| `carimbo` | `texto`, `cor`? | faixa de baixo | frase de impacto |
| `selo` | `texto`, `cor`? | faixa de baixo | etiqueta curta (ex.: "DICA DE CONSOLE") |
| `parte2` | `texto`?, `sub`? | faixa de baixo | chamada final |

Cores em hexadecimal. A cor padrão segue o jogo: Valorant `#FF4655`, Fortnite `#508CFF`.

## Roteiro falado (voz grátis)

- Português do Brasil, frases curtas, sem etiquetas entre colchetes.
- Nomes do jogo como são falados: "Vandal", "Phantom", "Operator", "Jett", "Ascent", "zero build". Evite siglas obscuras.
- Números por extenso quando forem importantes ("dois tiros na cabeça").

## Entrega (postagem manual pelo dono)

**Não agende no Metricool.** O plano grátis do Metricool só permite 20 posts por mês e a cota acabou; o dono decidiu postar
à mão pelo app do TikTok. Cada execução entrega:

1. O arquivo `episodios/<pasta>/video.mp4`, enviado ao dono com a ferramenta de enviar arquivo (SendUserFile).
2. Uma mensagem (SendUserMessage) pronta para copiar, neste formato:
   - **Horário para postar:** 14:00 (Fortnite) ou 19:00 (Valorant)
   - **Título:** `titulo`
   - **Texto do post:** `legenda` + linha em branco + hashtags com `#` (num bloco de código, para copiar fácil)
   - Lembrete: não marcar "conteúdo gerado por IA" (decisão do dono).
3. Uma notificação push curta: "Vídeo de <jogo> pronto: <titulo>. Abre a conversa pra baixar e postar às <horário>."

No `historico.md`, use o horário do slot e escreva "entregue para postar" no tema.

## Análise de desempenho (toda segunda-feira, na tarefa das 13h55)

Antes de produzir, puxe pelo Metricool as métricas dos vídeos do TikTok dos últimos 7 dias (visualizações, curtidas,
comentários, compartilhamentos, tempo assistido se houver). Compare por jogo, tipo de tema, tipo de gancho e duração.
Atualize `fabrica/aprendizados.md` com 3 a 6 conclusões objetivas (o que repetir, o que evitar) e use-as daqui pra frente.

## Preparar gameplay nova (feito manualmente com o dono)

```
python fabrica/preparar_gameplay.py <arquivo.mp4> valorant   # ou fortnite
```

Corta em clipes de 30 s e gera fichas em `gameplay/<jogo>/fichas/`. Olhe as fichas e descreva cada clipe no `catalogo.json`.
