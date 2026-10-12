# Estudo com usuários (Fase 6)

O participante recebe um link, `https://tcc-undb.vercel.app` (a raiz do site),
e faz tudo pelo navegador, sem sessão marcada:

1. Lê e aceita o termo de consentimento.
2. Responde a um perfil curto, sem dados que o identifiquem.
3. Responde a 4 perguntas usando uma das ferramentas, embutida na própria
   página: o painel do Power BI ("Publicar na Web") ou o Indaga.
4. Responde ao questionário SUS sobre essa ferramenta.
5. Repete os passos 3 e 4 com a outra ferramenta e outras 4 perguntas.
6. Diz qual ferramenta prefere para cada tipo de pergunta e deixa comentários.

Tudo é gravado no Supabase, nas tabelas `indaga.estudo_*`. As consultas que
o participante faz ao Indaga ficam em `indaga.execucoes`, com
`origem = 'estudo'`.

## Desenho

- **Intrassujeito com contrabalanceamento:** cada pessoa usa as duas
  ferramentas, e o grupo dela define a ordem das ferramentas e o conjunto de
  perguntas que vai com cada uma.

  | Grupo | Primeira parte | Segunda parte |
  |---|---|---|
  | 0 | Painel com X | Indaga com Y |
  | 1 | Indaga com X | Painel com Y |
  | 2 | Painel com Y | Indaga com X |
  | 3 | Indaga com Y | Painel com X |

  Cada participante novo entra no grupo que tem menos gente no momento.
- **Conjuntos equivalentes:** cada conjunto tem uma pergunta de cada tipo, em
  pares, definidos em `config/estudo.json`.

  | Tipo | Conjunto X | Conjunto Y |
  |---|---|---|
  | A | A1 Faturamento de 2017 | A2 Pedidos em 2018 |
  | B | B1 Faturamento SP, 2º sem. 2017 | B4 beleza_saude em nov. 2017 |
  | C | C4 Clientes que recompraram | C3 Parcelas médias no cartão |
  | D | D1 Lucro líquido | D3 Meta de 2018 |
- **Tempo:** começa quando a ferramenta termina de carregar e vai até o envio
  da resposta. Assim, a demora para carregar o Power BI não pesa contra o
  painel. Se a pessoa fechar e reabrir a página, o cronômetro continua de onde
  estava, sem zerar.
- **Custo:** no Indaga, só são aceitas perguntas do bloco do Indaga que ainda
  não foram respondidas, com no máximo 8 consultas por pergunta.

## O que é medido

| Nível | Métricas |
|---|---|
| Pergunta | tempo; resposta; acerto (`analisar_estudo.py`); confiança de 1 a 5; se conferiu; "os dados não permitem" ou "não consegui" |
| Pergunta, só no Indaga | número de consultas; se a última resposta da IA estava certa; se abriu o SQL; viés de automação |
| Ferramenta | SUS (0 a 100) |
| Participante | perfil; preferência por tipo de pergunta; em qual confiou mais; comentários |

Limitação: no painel do Power BI não dá para registrar os cliques, porque a
página embutida é da Microsoft e o navegador não deixa a página do estudo ler
o que acontece dentro dela.

## Antes de publicar

1. **Termo de consentimento:** preencha título, pesquisador, orientador e
   contato em `config/estudo.json` (bloco `termo`) e peça ao orientador para
   revisar o texto, que está em `static/estudo.html`, na função `telaTermo`.
2. **CEP:** confirme com a coordenação se a pesquisa precisa ou não de
   aprovação.
3. **SUS:** os 10 itens em `static/estudo.html` são uma tradução de trabalho.
   Confira com a adaptação brasileira publicada que você for citar e ajuste o
   texto se for preciso.
4. **Congelamento:** o dashboard publicado precisa ser a versão congelada, e o
   Indaga, a mesma configuração (`config_hash`) da Fase 5.
5. **Limite de gasto:** defina um limite mensal no console da Anthropic
   (Settings > Limits). O link é público.

## Publicar na Vercel

O FastAPI roda na Vercel sem adaptação: ela detecta o `app.py` na raiz. O
`vercel.json` só aumenta o tempo máximo da função para 300 s, porque uma
resposta do Indaga pode levar até 60 s. A versão do Python fica fixada no
`.python-version`.

1. O código está em https://github.com/ArivaldoFilho/tcc-undb (público). O
   `.env`, a pasta `dados/` e o `.docx` do TCC ficam fora do Git (`.gitignore`).
2. Na Vercel, importe o repositório (*Add New > Project*). O projeto
   `tcc-undb` já existe na conta.
3. Em *Settings > Environment Variables*, cole o conteúdo do `.env` (a Vercel
   aceita colar o arquivo inteiro). Confira se aparecem `ANTHROPIC_API_KEY`,
   `DATABASE_URL`, `DATABASE_URL_LEITURA`, `INDAGA_MODELO` e `INDAGA_ESFORCO`,
   com os mesmos valores da Fase 5, e acrescente uma `INDAGA_SENHA_ACESSO`
   nova, que protege a interface livre em `/`.
4. Faça um novo deploy. Abra `https://tcc-undb.vercel.app/?piloto=1`. A interface livre do Indaga fica em `/indaga`, com a senha `INDAGA_SENHA_ACESSO`.

Cada push no `main` gera um deploy novo. **Depois que a coleta começar, não
envie mudanças para o `main`**, porque isso trocaria o sistema no meio do
estudo.

## Piloto

- Use o link com `?piloto=1`. Os participantes do piloto recebem códigos T001,
  T002... e ficam fora da análise principal.
- `?novo=1` começa uma sessão nova no mesmo navegador. Use isso para testar
  várias vezes, ou quando duas pessoas usarem o mesmo computador.
- Faça 2 pilotos e depois rode:
  ```
  .venv\Scripts\python avaliacao\analisar_estudo.py --piloto
  ```

## Coleta e análise

- Link para os participantes: `https://tcc-undb.vercel.app`.
- Para acompanhar a coleta e gerar os arquivos de análise:
  ```
  .venv\Scripts\python avaliacao\analisar_estudo.py
  ```
  Ele gera, em `avaliacao/resultados/`: `estudo_respostas.csv`,
  `estudo_resumo.csv` (ferramenta x tipo), `estudo_pareado.csv` (entrada do
  Wilcoxon) e `estudo_participantes.csv`. Os critérios de correção estão no
  topo do script.
- Se alguém pedir a exclusão dos dados pelo código, apague as linhas desse
  participante em `estudo_eventos`, `estudo_sus`, `estudo_respostas` e
  `estudo_participantes`, e as execuções dele em `indaga.execucoes`.
