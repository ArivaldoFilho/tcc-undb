# Banco de perguntas (Fase 4)

São 26 perguntas candidatas: 6 do tipo A, 6 do tipo B, 7 do tipo C e 7 do
tipo D. O plano prevê de 16 a 20 na versão final. Escolha as definitivas,
apague as linhas das outras em `perguntas.csv` e em `dashboard.csv` e só
depois congele os dois arquivos.

- `perguntas.csv` é lido por `rodar.py` e por `corrigir.py` (Solução B).
- `dashboard.csv` é a ficha da avaliação no painel (Solução A). As colunas
  `*_previsto` justificam o tipo de cada pergunta; as demais são preenchidas
  na Fase 5.

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

| Critério | Quando é correto | Perguntas |
|---|---|---|
| numero | Resultado com uma linha e alguma célula igual ao gabarito, dentro da tolerância | A1-A3, B1-B6, C3, C4 |
| percentual | Como numero; aceita a resposta em pontos (6,63) ou em fração (0,0663) | A6 |
| lista | Alguma coluna do resultado tem exatamente o conjunto do gabarito; a ordem não conta | A4, A5, C5, C6 |
| recusa | A decisão foi sem_dados ou esclarecimento | D1-D4 |
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

## Antes de congelar

1. Escolha de 16 a 20 perguntas, mantendo pelo menos 4 de cada tipo.
2. Peça ao orientador para conferir os gabaritos. Os SQLs estão em
   `perguntas.csv`.
3. Peça a uma pessoa de fora para revisar as perguntas do tipo C, para ver se
   são perguntas que um gestor faria de fato.
4. Rode um piloto curto para conferir o formato, com 1 repetição e só algumas
   perguntas:
   ```
   .venv\Scripts\python avaliacao\rodar.py --rodada piloto --repeticoes 1 --ids A1,B2,C4,D1
   .venv\Scripts\python avaliacao\corrigir.py --rodada piloto
   ```
   O piloto não entra nos resultados e não deve levar a ajustes de prompt
   voltados a essas perguntas.

## Para a Fase 6 (estudo com usuários)

O desenho intrassujeito precisa de **dois conjuntos equivalentes**, um por
ferramenta. Quando as perguntas finais estiverem escolhidas, monte os
conjuntos X e Y com o mesmo número de perguntas de cada tipo e dificuldade
parecida. Exemplo de par: B2 (ticket RJ 2018) em X e uma variação com outra
UF e outro ano em Y.
