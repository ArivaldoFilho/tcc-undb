# Banco de perguntas (Fase 4)

- `perguntas_candidatas.csv`: as 32 candidatas (26 iniciais e 6 armadilhas).
- `perguntas.csv`: a **seleção final de 20** (4 A, 6 B, 6 C e 4 D). É lido por
  `rodar.py` e `corrigir.py` (Frente A).
- Para trocar uma pergunta, copie a linha das candidatas para `perguntas.csv`
  (e para `dashboard.csv`) e só depois congele os dois arquivos.
- `dashboard.csv` é a ficha do painel (Solução A). As colunas `*_previsto`
  justificam o tipo de cada pergunta; `responde`, `passos`, `valor_lido` e
  `esforco_adaptacao` (0 a 3) são preenchidas na Frente A (ver
  `docs/AVALIACAO.md`, A6).

## Como as perguntas foram classificadas

O tipo de cada pergunta é definido em relação ao dashboard congelado, e não
pela dificuldade da pergunta.

| Tipo | Critério operacional |
|---|---|
| A. Prevista | Um único visual do painel responde, com no máximo um segmentador selecionado |
| B. Variação | O painel responde, mas exige dois ou mais filtros combinados |
| C. Não prevista | Nenhum visual do painel responde, porque falta a medida, a dimensão ou o cruzamento |
| D. Ambígua ou sem resposta | A base não tem o dado, ou a pergunta admite mais de uma leitura |

Isso dá a definição operacional pedida pela banca: "exploratória" equivale
aos tipos B e C.

**Versão do dashboard usada na classificação:** hash `650a8b665c17` dos
arquivos de `dashboard/` (relatório, modelo e SQL), 12 out. 2026. Se o painel
mudar antes do congelamento (por exemplo, se o segmentador de Semestre for
removido), revise os tipos e os caminhos em `dashboard.csv`. B1 continua do
tipo B, porque também pode ser respondida selecionando os meses de jul a dez.

## Critérios de acerto (definidos antes da coleta)

As colunas de perguntas abaixo listam as 26 candidatas iniciais. As armadilhas estão na seção própria.

| Critério | Quando é correto | Perguntas |
|---|---|---|
| numero | Resultado com uma linha e alguma célula igual ao gabarito, dentro da tolerância | A1-A3, B1-B6, C3, C4 |
| percentual | Como numero; aceita a resposta em pontos (6,63) ou em fração (0,0663) | A6 |
| lista | Alguma coluna do resultado tem exatamente o conjunto do gabarito; a ordem não conta | A4, A5, C5, C6 |
| recusa | A decisão foi sem_dados ou esclarecimento; se a IA executou SQL e explicou, vai para revisão manual (D4.8) | D1-D4 |
| rubrica | Correção manual pelo texto da coluna observacao | C1, C2, C7, D5-D7 |

### Tolerâncias

- **Valores em reais:** 0,01, que absorve o arredondamento em centavos.
- **Médias de nota e de parcelas:** 0,01, que aceita duas casas decimais.
- **Prazo em dias:** 0,05, que aceita a leitura com uma casa no painel. Calcular o prazo com a hora (em vez
  da diferença de datas) dá 21,70 em B3, contra 21,63 no gabarito, e é
  corrigido como erro de definição.
- **Percentual:** 0,1 ponto percentual.
- **Contagens:** zero.

## Gabaritos (conferidos no banco em 12 out. 2026)

| Id | Gabarito | O que a pergunta testa |
|---|---|---|
| A1 | R$ 6.108.492,27 | Definição de faturamento |
| A2 | 53.532 pedidos | Pedido válido (sem filtro dá 54.011) |
| A3 | 4,0864 | Média simples |
| A4 | SP, RJ, MG, RS, PR | Ranking (6º: SC) |
| A5 | beleza_saude, relogios_presentes, cama_mesa_banho, esporte_lazer, informatica_acessorios | Ranking (6º: moveis_decoracao) |
| A6 | 6,63% | Atraso sobre entregues |
| B1 | R$ 1.458.780,39 | Período + UF |
| B2 | R$ 138,32 | Nome do estado para sigla; razão entre duas medidas |
| B3 | 21,63 dias | Definição de prazo |
| B4 | R$ 78.976,65 | Categoria + mês |
| B5 | 23.051 clientes | customer_unique_id (com customer_id dá 23.599) |
| B6 | 3,8298 | Nota pelo ano da compra |
| C1 | nota 1: 37,76% atrasados; nota 5: 3,00% | Cruzamento nota x atraso |
| C2 | credit_card (76.505 pedidos) | Tabela que o painel não usa |
| C3 | 3,5072 parcelas | Tabela que o painel não usa |
| C4 | 2.888 clientes | Recompra por customer_unique_id |
| C5 | 5 seller_id (5º: R$ 97.828,71; 6º: R$ 97.311,03) | Ranking sensível ao filtro de pedido válido |
| C6 | sao paulo | Dimensão que o painel não exibe |
| C7 | acima de 5 kg: R$ 39,78; até 5 kg: R$ 17,21 | Atributo de produto não modelado |
| D1-D4 | recusa | Lucro, data fora da base, meta, estoque |
| D5-D7 | rubrica | Ambiguidade e período sem dados |

## Perguntas-armadilha (acrescentadas em 12/10/2026)

O teste de auditoria mostrou risco de efeito teto: a IA acertou todas as
perguntas iniciais testadas. Foram acrescentadas 6 perguntas realistas, cada
uma com uma dificuldade conhecida. **Elas não foram testadas na IA antes de
entrar no banco:** escolher perguntas porque a IA erra nelas seria um viés de
seleção.

| Id | Dificuldade | Correto | Resposta ingênua |
|---|---|---|---|
| B7 | Qualidade de dados: o último trimestre "na data" (T3 2018) está incompleto | T2 2018: R$ 2.849.730,26 | T3 sem aviso: R$ 1.727.049,37 |
| B8 | Conhecimento de domínio: Nordeste = 9 UFs | 4.713 clientes | 4.799 (customer_id) |
| C8 | Fan trap: junção de itens com pagamentos | R$ 206.928,31 | R$ 315.312,64 (+52%) |
| C9 | Mudança de definição: ticket com frete | R$ 159,77 | R$ 137,64 (sem frete) |
| C10 | Várias etapas: taxa por UF com corte de volume | CE | AL (sem o corte) |
| C11 | Granularidade: média por pedido, não por pagamento | R$ 160,56 | R$ 154,81 |

## Seleção final (20)

| Tipo | Perguntas | Por que estas |
|---|---|---|
| A | A1, A2, A5, A6 | Número, lista e percentual |
| B | B1, B3, B4, B5, B7, B8 | Filtros combinados, definições (B3, B5), qualidade de dados (B7) e domínio (B8) |
| C | C1, C3, C4, C8, C9, C11 | Cruzamento analítico (C1), tabela fora do painel (C3), recompra (C4) e três armadilhas |
| D | D1, D2, D3, D5 | Dado inexistente (D1, D3), data fora da base (D2) e ambiguidade (D5) |

Ficaram de fora: A3 e A4 (parecidas com A1 e A5), B2 e B6 (parecidas com B3 e
B5), C2, C5, C6, C7 e C10 (C6 dá para adivinhar sem dados; C5 exige digitar
ids longos; C2 e C7 aumentariam a correção manual), D4, D6 e D7 (repetem D1,
D5 e D2). Tipos B e C têm mais perguntas porque são os "exploratórios" da
hipótese.

## Antes de congelar

1. Escolha de 16 a 20 perguntas, mantendo pelo menos 4 de cada tipo.
2. Peça ao orientador para conferir os gabaritos. Os SQLs estão em
   `perguntas.csv`.
3. Peça a uma pessoa de fora para revisar as perguntas do tipo C, para ver se
   são perguntas que um gestor faria de fato.
4. Rode um piloto curto para conferir o formato, com 1 repetição e só algumas
   perguntas:
   ```
   .venv\Scripts\python avaliacao\rodar.py --rodada piloto --repeticoes 1 --ids A1,B3,C4,D1
   .venv\Scripts\python avaliacao\corrigir.py --rodada piloto
   ```
   O piloto não entra nos resultados e não deve levar a ajustes de prompt
   voltados a essas perguntas.
