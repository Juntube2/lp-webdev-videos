# Manual de produção — TikTok LP Web Dev

Este manual é seguido pelas tarefas agendadas que produzem e agendam os vídeos sozinhas
(14h e 19h, horário de São Paulo). Cada execução produz **um** episódio.

## Visão geral do fluxo

1. Ler `fabrica/historico.md` (o que já foi ao ar) e `fabrica/pautas.md` (ideias).
2. Escolher um tema que **não** esteja no histórico e escrever o roteiro.
3. Criar `episodios/<AAAA-MM-DD>-<14h|19h>-<slug>/episodio.json` e fazer commit + push na `main`.
4. O GitHub Actions (`.github/workflows/renderizar.yml`) narra no ElevenLabs e monta o vídeo.
   Ao terminar, aparecem `episodios/<pasta>/video.mp4`, `status.json` e `videos/<pasta>.mp4`.
5. Conferir o vídeo (extrair quadros e olhar).
6. Agendar no Metricool (TikTok) para o horário do slot.
7. Acrescentar uma linha em `fabrica/historico.md`, commit + push.

## Linha editorial

- **Foco: ensinar programação** para iniciantes (lógica, HTML/CSS, JavaScript, Python, Git, carreira de dev, ferramentas).
- **Cerca de 1 a cada 5 vídeos fala de sites para negócios** (por que ter site, site x Instagram, o que um bom site precisa),
  sempre com tom educativo, sem vender serviço de forma agressiva.
- Tom: amigo que já passou por isso, direto, divertido, sem gíria pesada e sem palavrão.
- Proibido: prometer renda garantida ("ganhe R$ 10 mil"), citar pessoas reais, imitar marcas/personagens de terceiros,
  usar dados que você não tem certeza. Conteúdo técnico tem que estar **correto**.

## Regras do roteiro

- Português do Brasil, falado, frases curtas. **500 a 650 caracteres** (≈ 35–45 s de áudio).
- Estrutura: **gancho** na primeira frase (curiosidade, erro comum, "se eu fosse...", "pare de...") →
  2 a 4 pontos numerados ou um passo a passo → **chamada final** (seguir, salvar, comentar, "parte 2").
- Comece o roteiro com uma etiqueta de emoção do ElevenLabs, por exemplo `[animado]`. Use no máximo 2 etiquetas no texto.
- Escreva siglas como devem ser lidas quando houver dúvida (ex.: "API" pode ficar; "SQL" escreva "SQL").
- Evite números com vírgula decimal e símbolos (%, R$) no roteiro falado: escreva por extenso ("vinte por cento").

## Formato do `episodio.json`

```json
{
  "titulo": "Título curto para o TikTok (até 60 caracteres)",
  "roteiro": "[animado] Texto completo da narração...",
  "legenda": "Legenda do post com 1 frase + chamada. Sem hashtags aqui.",
  "hashtags": ["programacao", "aprenderaprogramar", "javascript", "dev", "lpwebdev"],
  "cenas": [
    {"inicio": "", "fundo": 0, "expressao": "oculos", "elementos": []},
    {"inicio": "Primeiro", "fundo": 1, "expressao": "bravo", "elementos": [{"tipo": "numero", "texto": "1"}]}
  ]
}
```

### Cenas

- Uma cena nova a cada **2 a 4 segundos** de fala (8 a 12 cenas por vídeo). A primeira cena tem `"inicio": ""`.
- `inicio`: a **palavra exata do roteiro** em que a cena começa (sem pontuação, maiúsculas não importam).
  As palavras de início têm que aparecer **na ordem** do roteiro. Escolha palavras que só apareçam uma vez naquele trecho.
- `fundo`: 0 a 4 (tons diferentes do fundo de código). Alterne entre cenas.
- `expressao` da onça: `confiante`, `pensando`, `rindo`, `bravo`, `oculos`, `surpreso`.
  Combine com a fala (dúvida → pensando; erro → bravo; revelação → surpreso; gancho e final → oculos).
- `elementos`: 0 a 3 por cena. Varie bastante; não repita o mesmo tipo em cenas seguidas.

### Tipos de elemento

| tipo | campos | uso |
| --- | --- | --- |
| `numero` | `texto` ("1"), `cor`? | marcar passos |
| `selo` | `texto` (curto: "JS", "HTML"), `cor`, `cor_texto`?, `tamanho`? | logo de linguagem/ferramenta (só texto, sem logo oficial) |
| `chips` | `itens` (até 5) | conceitos que aparecem um a um |
| `riscado` | `texto` | mito ou erro (com X vermelho) |
| `carimbo` | `texto`, `cor`? | frase de impacto |
| `navegador` | `titulo`, `url`, `cor`, `botao`? | site fictício (negócio inventado) |
| `codigo` | `linhas` (até 8, curtas, até ~30 caracteres) | trecho de código correto |
| `grafico` | `texto`, `valores`? | crescimento / dinheiro |
| `versus` | `a`, `b`, `cor_a`?, `cor_b`? | comparação |
| `lista` | `itens` (até 5), `marcar` ("check" ou "x") | checklist |
| `texto` | `texto`, `cor`?, `cor_texto`? | cartão com frase |
| `parte2` | `texto`?, `sub`? | chamada final |

Cores em hexadecimal, ex. `"#3FB27F"`. Sugestões: JavaScript `#F0DB4F` (texto `#1E1E1E`), HTML `#E34F26`, CSS `#264DE4`,
Python `#3776AB`, Git `#F05032`, verde LP `#3FB27F`, vermelho TikTok `#FE2C55`.

## Testar localmente (opcional)

```
pip install pillow numpy scipy   # e ffmpeg instalado
ELEVENLABS_API_KEY=... python fabrica/narrar.py episodios/<pasta>
python fabrica/montar.py episodios/<pasta>
```

## Agendamento no Metricool

- Marca (blogId): `7800532`, rede `tiktok`, fuso `America/Sao_Paulo`.
- Mídia: `https://raw.githubusercontent.com/Juntube2/lp-webdev-videos/main/videos/<pasta>.mp4`
- Texto: `legenda` + linha em branco + hashtags com `#`.
- `tiktokData`: `title` = `titulo`, `privacyOption` = `PUBLIC_TO_EVERYONE`, `isAigc` = **false**
  (decisão do dono da conta), `autoAddMusic` = false.
- Horário: o do slot (14:00 ou 19:00). Se já tiver passado, agende para daqui a 10 minutos.

## Histórico

`fabrica/historico.md` tem uma linha por vídeo: data, horário, pasta, título, tema. Nunca repita um tema já publicado
nos últimos 30 dias; variações e "parte 2" de um tema são permitidas se continuarem o anterior.
