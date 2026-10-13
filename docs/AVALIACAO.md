# Fluxo de coleta e testes

São quatro frentes:
- **A. Avaliação técnica** com as 20 perguntas do banco.
- **B. Questionário**, em paralelo com a Frente A.
- **C. Perguntas escritas pelos participantes**, testadas depois que o
  questionário fechar.
- **D. Consolidação** de tudo na matriz de decisão.

**Regra geral:** a configuração do Indaga (modelo, prompts, descrições do
esquema, `config_hash`) e o painel ficam **congelados** do início da Frente A
até o fim da Frente C. Qualquer mudança feita depois de ver resultados vai
para o [DECISOES.md](DECISOES.md), com data e motivo.

Os comandos abaixo são rodados na raiz do projeto, com `.venv\Scripts\python`.

## Etapa 0. Pré-requisitos

Nada roda antes disso.

| Item | Situação |
|---|---|
| Cartões do painel conferidos e painel congelado (registrar a data) | Visão geral conferida; faltam Vendas e Entrega (`dashboard/README.md`) |
| Gabaritos das 20 perguntas conferidos pelo orientador | Pendente |
| Coluna `coberta_pela_documentacao` preenchida nas 20 perguntas | Feito pelo autor (B7, B8, D2 e D5 = nao); conferir junto com os gabaritos |
| Rubricas das perguntas do tipo D escritas | Feito: coluna `observacao` de D1, D2, D3 e D5 em `avaliacao/perguntas.csv` |
| Configuração do Indaga congelada; `config_hash` anotado | Pendente; hash atual `0bf3b7d7bed6b8ac` |
| Usuário do banco somente leitura para o Indaga | Feito: `indaga_leitor` |
| Contagem de linhas registrada antes da coleta | Feito: `avaliacao/resultados/contagem_antes.csv`. Repetir no dia, se a base for recarregada |
| Teto de gasto na chave da API | Pendente: console da Anthropic, Settings > Limits |
| Limite de uso no Indaga público | Feito: 100 consultas a cada 24 h (`INDAGA_LIMITE_DIARIO`) |
| Orientador consultado sobre o Comitê de Ética | Pendente |
| Formulário aberto (registrar data e canais) | Pendente |

```
python scripts/contar_linhas.py antes
```

## Frente A. Avaliação técnica com as 20 perguntas do banco

**A1. Rodar.** As 20 perguntas, 5 vezes cada, em rodadas intercaladas (todas
na repetição 1, depois todas na 2...). Cada execução é uma sessão nova, sem
histórico. A data e o identificador do modelo devolvido pela API ficam em cada
linha do `.jsonl`. Rodar numa janela curta, de preferência no mesmo dia.
```
python avaliacao/rodar.py --rodada final --repeticoes 5
```

**A2. Falhas de API.** O `rodar.py` faz uma nova tentativa. Se falhar de novo,
a execução vira **erro de execução**, que fica fora da taxa de acerto.

**A3. Correção automática** pelo critério de cada pergunta.

A **unidade de correção é a execução**: uma pergunta numa repetição, e cada
uma recebe um veredito. O veredito é sobre a **resposta que o usuário recebe**
(resultado e explicação), e não sobre o SQL: um SQL diferente do gabarito que
chega ao mesmo resultado está certo. A correção automática, porém, compara só
o resultado com o gabarito. A explicação é conferida na revisão manual (A4 e
A5), pelas recusas e rubricas, pelos números citados que não aparecem no
resultado e pela amostra de acertos automáticos.
```
python avaliacao/corrigir.py --rodada final
```

**A4 e A5. Revisão manual.** O `corrigir.py` gera o `final_revisao.csv`, com:
- as recusas e rubricas, que pedem julgamento;
- os erros, para reconferir o gabarito antes de contar o erro;
- as explicações com números que não aparecem no resultado (alucinação na
  etapa de texto);
- uma **amostra dos acertos automáticos**: uma execução sorteada por pergunta
  entre as corretas pelo critério (`--amostra` muda a quantidade). O sorteio
  usa uma semente fixa, o nome da rodada, e não muda ao rodar de novo. A
  amostra estima quantos acertos automáticos são falsos (resultado certo pela
  razão errada, ou explicação errada); o `corrigir.py` imprime quantas foram
  revertidas.

O autor e um segundo avaliador preenchem `avaliador_1` e `avaliador_2`, cada
um sem ver o outro. O consenso vai em `veredito_final`, e `explicacao_errada`
recebe "sim" quando o resultado está certo e o texto está errado. Uma correção
de gabarito vai para `perguntas.csv` e para o DECISOES.md. Depois, rodar de
novo o `corrigir.py`: ele aplica os vereditos e preserva o que já foi
preenchido.
```
python avaliacao/concordancia.py avaliacao/resultados/final_revisao.csv
python avaliacao/corrigir.py --rodada final
```

**A6. Painel.** O autor preenche o `avaliacao/dashboard.csv` para as 20
perguntas:
- `responde`: sim, parcial ou nao;
- `passos`: número de filtros e cliques;
- `valor_lido`: o valor encontrado no painel;
- `esforco_adaptacao`: o que seria preciso mudar no painel, numa escala de
  0 a 3.

| Esforço | Significado |
|---|---|
| 0 | Nenhuma mudança |
| 1 | Nova medida DAX |
| 2 | Novo visual |
| 3 | Mudança no modelo de dados |

**A7. Conferir a base** depois da coleta. A contagem precisa ser igual à de
antes.
```
python scripts/contar_linhas.py depois
```

**Saídas**, todas em `avaliacao/resultados/`: `final.jsonl` (o log),
`final_execucoes.csv`, `final_revisao.csv`, `final_resumo.csv` e o
`dashboard.csv` preenchido.

## Frente B. Questionário

Roda em paralelo com a Frente A, num formulário externo (Google Forms ou
equivalente).

**B1. Divulgar** em canais variados: gestores e profissionais de dados, não só
colegas de curso. Registrar os canais e as datas.

**B2. Meta:** pelo menos 20 respostas, idealmente 30.

**B3. Fechar o formulário** e registrar a data.

**B4. Exportar** as respostas em CSV para `dados/questionario/original.csv` e
não alterar esse arquivo. A pasta `dados/` fica fora do Git, porque as
respostas podem conter dados pessoais.

**B5. Limpar** num arquivo separado (`dados/questionario/limpo.csv`). Retirar
quem não deu consentimento, as respostas duplicadas e as vazias, e registrar
cada exclusão com o motivo.

**B6. Análise descritiva**, cruzada com a área de atuação:
- perfil (área);
- frequência de uso de dashboards;
- frequência de perguntas que o painel não responde, e quem atende essas
  perguntas;
- tempo para incluir uma métrica nova;
- uso de IA;
- confiança em decisões rotineiras e em decisões importantes;
- fluxo preferido.

**Saídas:** o CSV original, o CSV limpo e as tabelas e gráficos de
frequência.

## Frente C. Perguntas escritas pelos participantes

Começa depois do fechamento do formulário (B3).

**C1. Extrair** todas as perguntas, até 3 por participante, para o
`avaliacao/perguntas_participantes.csv`. O arquivo tem as mesmas colunas do
banco e mais `participante`, `tipo_autor`, `tipo_segundo` e `triagem`.

**C2. Triagem,** registrando o motivo de cada decisão na coluna `triagem`:
- juntar perguntas idênticas ou quase idênticas;
- **não** descartar as perguntas que a base não responde, porque elas são do
  tipo D;
- descartar só as incompreensíveis ou fora do tema de vendas.

**C3. Classificar** cada pergunta nos tipos A a D, em relação ao painel
congelado. O autor preenche `tipo_autor` e um segundo classificador preenche
`tipo_segundo`. As divergências são resolvidas por consenso na coluna `tipo`.
O autor também preenche `coberta_pela_documentacao`, com o mesmo critério das
perguntas do banco (D1).
```
python avaliacao/concordancia.py avaliacao/perguntas_participantes.csv --colunas tipo_autor tipo_segundo
```

**C4. Gabarito em SQL** para as perguntas que a base responde, com as mesmas
definições de `config/descricoes.json`. O orientador confere uma amostra.

**C5. Rodar no Indaga com o texto literal do participante,** sem corrigir nem
reescrever, porque é isso que mede o uso real. São 3 repetições, com a mesma
configuração e o mesmo `config_hash` da Frente A.
```
python avaliacao/rodar.py --rodada participantes --repeticoes 3 --arquivo avaliacao/perguntas_participantes.csv
```

**C6. Corrigir** como em A3 a A5:
```
python avaliacao/corrigir.py --rodada participantes --arquivo avaliacao/perguntas_participantes.csv
```

**C7. Painel:** preencher o `avaliacao/dashboard_participantes.csv` como em A6.

## Frente D. Consolidação

**D1. Matriz de decisão** por tipo de pergunta, com o acerto e a consistência
da IA, o tempo, o custo, a cobertura do painel e o esforço de adaptação. Uma
matriz para as perguntas do banco e outra para as dos participantes, e as duas
lado a lado.

A matriz também separa os resultados pela coluna `coberta_pela_documentacao`:
- **sim:** tudo o que a pergunta exige (definição, coluna, armadilha) está
  escrito em `config/descricoes.json`;
- **nao:** acertar exige conhecimento ou inferência que a documentação não
  traz (domínio, qualidade dos dados, ambiguidade).

A diferença de acerto entre as duas linhas mostra quanto do desempenho da IA
vem da documentação preparada e quanto do raciocínio do modelo.
```
python avaliacao/matriz.py --rodada final
python avaliacao/matriz.py --rodada participantes --arquivo avaliacao/perguntas_participantes.csv --painel avaliacao/dashboard_participantes.csv
```

**D2. Cruzar com o questionário:**
- a proporção de perguntas reais que o painel não previa;
- o tempo declarado para incluir uma métrica nova;
- a confiança declarada para decisões rotineiras e importantes.

**D3. Listar os resultados que contrariam a hipótese.**

**D4. Guardar** os logs, os CSVs e o `config_hash`. Os arquivos de
`avaliacao/resultados/` vão para o repositório. As respostas brutas do
questionário ficam fora, em `dados/`.

## Ordem no tempo

1. Etapa 0.
2. Frentes A e B em paralelo.
3. Fechamento do formulário (B3), depois a Frente C.
4. Frente D.

## Referência rápida

| Arquivo | Conteúdo |
|---|---|
| `avaliacao/perguntas.csv` | As 20 perguntas do banco, com gabarito, critério, rubrica e `coberta_pela_documentacao` |
| `avaliacao/perguntas_candidatas.csv` | As 32 candidatas de onde saíram as 20 |
| `avaliacao/BANCO_DE_PERGUNTAS.md` | Tipos, critérios, tolerâncias, armadilhas e gabaritos |
| `avaliacao/dashboard.csv` | Ficha do painel (A6) |
| `avaliacao/perguntas_participantes.csv`, `dashboard_participantes.csv` | Frente C (modelos vazios) |
| `avaliacao/rodar.py`, `corrigir.py` | Execução e correção (A e C) |
| `avaliacao/concordancia.py` | Concordância entre dois julgadores (A5 e C3) |
| `avaliacao/matriz.py` | Matriz de decisão (D1) |
| `scripts/contar_linhas.py` | Contagem da base antes e depois (Etapa 0 e A7) |
| `config/descricoes.json` | Definições de métrica compartilhadas pelas duas soluções |
