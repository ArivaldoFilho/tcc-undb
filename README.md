# Indaga

Código do TCC "dashboard x IA generativa na análise de dados" (Engenharia de
Software, UNDB). Compara duas formas de responder a perguntas de negócio sobre
a mesma base (Olist, no PostgreSQL):

- **Solução A, dashboard:** painel no Power BI (`dashboard/`).
- **Solução B, Indaga:** o usuário pergunta em português, um LLM gera o SQL, e
  o resultado volta com tabela, gráfico, suposições e explicação.

As duas usam o mesmo banco e as mesmas definições de métrica
(`config/descricoes.json`).

O fluxo de coleta e testes está em **[docs/AVALIACAO.md](docs/AVALIACAO.md)**,
e as decisões, com os motivos, em [docs/DECISOES.md](docs/DECISOES.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `indaga/`, `app.py`, `static/` | Pipeline, servidor e interface do Indaga |
| `config/` | Definições de métrica compartilhadas |
| `banco/`, `scripts/` | Estrutura do banco, carga do Olist e contagem de linhas |
| `dashboard/` | Projeto do Power BI (PBIP) e o SQL do modelo |
| `avaliacao/` | Banco de perguntas, execução, correção, concordância, matriz e resultados |
| `docs/` | Fluxo de avaliação, registro de decisões e plano original |

## Como uma pergunta é respondida

```
pergunta
  └─ LLM com esquema, descrições e definições (sem nenhuma linha de dados)
       └─ decisão: sql | sem_dados | esclarecimento | conversa, com as suposições
            └─ (sql) guardrail: um único SELECT, sem comandos de escrita
                 └─ execução: usuário somente leitura, transação read-only, timeout 20 s
                      ├─ erro do banco → volta ao LLM, que corrige (até 2 vezes)
                      └─ resultado → LLM escreve a explicação (recebe até 50 linhas)
  └─ registro em indaga.execucoes: SQL, resultado, tokens, custo, tempo e config_hash
```

Escolhas que tornam o experimento reprodutível:
- sem cache, sem exemplos do histórico e com o esquema inteiro no prompt;
- temperatura não enviada, porque o `claude-opus-5-5` não aceita o parâmetro.
  O não determinismo é medido com repetições;
- falha da API: uma nova tentativa, feita pelo `rodar.py` e registrada no log.
  Se falhar de novo, a execução vira erro de execução;
- `config_hash` em cada execução, que prova que modelo, prompts e descrições
  não mudaram durante a coleta.

## Instalação

1. **Banco.** No SQL Editor do Supabase, rode `banco/01_estrutura.sql`, depois
   de trocar a senha do `indaga_leitor`.
2. **Dados.** Baixe o *Brazilian E-Commerce Public Dataset by Olist* (Kaggle) e
   descompacte em `dados/olist`.
3. **Ambiente.**
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   copy .env.example .env      (e preencha)
   .venv\Scripts\python scripts\carregar_olist.py dados\olist
   ```
4. **Interface.** Execute `iniciar.bat` e abra http://localhost:8010. A mesma
   interface está publicada na Vercel (`vercel.json`), com senha e um limite
   diário de consultas.

`GET /api/esquema` devolve o texto exato que o modelo recebe, para o apêndice.
