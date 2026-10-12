# Indaga

Protótipo da Solução B do TCC: o usuário pergunta em português, um LLM decide
como responder e, quando há dados para isso, gera uma consulta SQL. A consulta
roda num PostgreSQL com a base pública da Olist, e o resultado volta com a
tabela, um gráfico, as suposições adotadas e uma explicação em texto.

O dashboard da Solução A (Power BI) consulta o **mesmo banco** e usa as
**mesmas definições de métrica** de `config/descricoes.json`.

## Estrutura do repositório

| Pasta ou arquivo | Conteúdo |
|---|---|
| `app.py`, `indaga/` | Servidor e pipeline do Indaga (Solução B) |
| `static/` | Interface do Indaga (`index.html`) e página do estudo com usuários (`estudo.html`) |
| `config/` | Definições de métrica compartilhadas (`descricoes.json`) e configuração do estudo (`estudo.json`) |
| `banco/` | SQL da estrutura do banco e das tabelas do estudo |
| `scripts/` | Carga do Olist e criação das tabelas do estudo |
| `dashboard/` | Dashboard Power BI (Solução A) em formato PBIP, com o SQL do modelo; ver `dashboard/README.md` |
| `avaliacao/` | Banco de perguntas, avaliação técnica (Fase 5) e análise do estudo (Fase 6) |
| `docs/` | Plano das fases, registro de decisões (`DECISOES.md`) e guia do estudo (`ESTUDO.md`) |
| `vercel.json`, `.python-version` | Hospedagem na Vercel (estudo com usuários) |

## Fluxo de uma pergunta

```
pergunta
  └─ 1 chamada ao LLM com esquema + descrições + definições (sem dados)
       └─ decisão: sql | sem_dados | esclarecimento | conversa  + suposições
            └─ (sql) guardrail: um único SELECT/WITH, sem comandos de escrita
                 └─ execução: usuário somente leitura, transação read-only, timeout 20 s
                      ├─ erro do banco → o erro volta ao LLM, que corrige (até 2 vezes)
                      └─ resultado → 1 chamada ao LLM para a explicação (recebe até 50 linhas)
  └─ registro em indaga.execucoes: SQL, resultado, tokens, custo, tempo por etapa, config_hash
```

O que o modelo recebe:

- **Na decisão e no SQL:** apenas a estrutura das tabelas, as descrições, os relacionamentos e as definições. Nenhuma linha de dados.
- **Na explicação:** as linhas do resultado, até 50. Isso precisa constar na discussão sobre privacidade e LGPD.

### Escolhas para o experimento

| Escolha | Motivo |
|---|---|
| Sem cache de resultado | As repetições da mesma pergunta precisam ser chamadas reais ao modelo |
| Sem few-shot do histórico | Uma execução não pode "ensinar" a seguinte; as repetições ficam independentes |
| Esquema inteiro no prompt, sem busca vetorial | Com 9 tabelas cabe tudo; elimina uma fonte de variação |
| Sem retry automático do SDK | Toda chamada aparece no log e no tempo medido |
| Sem fallback de modelo em recusa | Uma troca silenciosa de modelo contaminaria os dados; a recusa é registrada como erro |
| Temperatura não enviada | O `claude-opus-5-5` não aceita o parâmetro. O não determinismo não pode ser zerado, só medido |
| `config_hash` em cada execução | Prova que modelo, esforço, prompts e descrições não mudaram durante a coleta |

## Instalação

1. **Supabase.** Crie o projeto. No SQL Editor, rode `banco/01_estrutura.sql`, depois de trocar a senha do `indaga_leitor`. Para o estudo com usuários, rode também `.venv\Scripts\python scripts\criar_estudo.py` (depois do passo 3).
2. **Dados.** Baixe o *Brazilian E-Commerce Public Dataset by Olist* no Kaggle e descompacte os CSVs numa pasta (por exemplo, `dados/olist`).
3. **Ambiente.**
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   copy .env.example .env      (e preencha)
   ```
4. **Carga.**
   ```
   .venv\Scripts\python scripts\carregar_olist.py dados\olist
   ```
   O script confere o cabeçalho de cada CSV, carrega, tenta criar as chaves estrangeiras e imprime as linhas por tabela. Anote esses números para o capítulo 3.
5. **Conferir as descrições.** Rode `SELECT DISTINCT order_status FROM olist.orders` e `SELECT DISTINCT payment_type FROM olist.order_payments` e confirme que os valores listados em `config/descricoes.json` batem com a base.
6. **Subir a interface.** Execute `iniciar.bat` e abra http://localhost:8010.

`GET /api/esquema` devolve o texto exato que o modelo recebe, pronto para o apêndice.

## Avaliação técnica (Fase 5)

1. Substitua os exemplos de `avaliacao/perguntas.csv` pelo banco de perguntas real, de 16 a 20 perguntas dos tipos A a D, com o SQL do gabarito e o critério de acerto. Os critérios estão descritos no topo de `avaliacao/corrigir.py`.
2. **Congele** `config/descricoes.json`, os prompts e o `.env`.
3. Rode:
   ```
   .venv\Scripts\python avaliacao\rodar.py --rodada final --repeticoes 5
   .venv\Scripts\python avaliacao\corrigir.py --rodada final
   ```
4. Resultados em `avaliacao/resultados/`:
   - `final_execucoes.csv`: uma linha por execução, com acerto, tempo, tokens, custo e os números da explicação que não aparecem no resultado (para revisão manual).
   - `final_resumo.csv`: por pergunta, taxa de acerto, consistência entre repetições, SQLs distintos, tempo mediano e custo médio.

Corrija à mão as perguntas com critério `rubrica` na coluna `situacao`.

## Esforço de configuração

Para comparar com as horas de construção do dashboard, registre o tempo gasto em:

- carga e conferência da base;
- escrita de `config/descricoes.json`;
- ajustes de prompt.

Não conte o desenvolvimento do código do Indaga: ele é reaproveitável para qualquer base, assim como o Power BI não entra nas horas do dashboard.
