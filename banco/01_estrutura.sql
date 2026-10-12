-- Indaga: estrutura do banco. Rodar UMA VEZ no SQL Editor do Supabase,
-- ANTES de scripts/carregar_olist.py.
--
-- Cria:
--   schema olist       dados da base (as tabelas são criadas pelo script de carga)
--   schema indaga      log de execuções
--   role indaga_leitor usuário somente leitura que executa o SQL gerado pela IA
--
-- Antes de rodar, troque TROQUE_ESTA_SENHA por uma senha forte e guarde-a
-- para o DATABASE_URL_LEITURA do .env.

create schema if not exists olist;
create schema if not exists indaga;

-- ── Log de execuções ─────────────────────────────────────────────────────
create table if not exists indaga.execucoes (
    id              bigserial primary key,
    criado_em       timestamptz not null default now(),
    origem          text not null,          -- interface | avaliacao
    rodada          text,                   -- nome da rodada de avaliação
    pergunta_id     text,                   -- id no banco de perguntas (A1, C3...)
    repeticao       int,
    participante    text,                   -- código anônimo no estudo com usuários
    pergunta        text not null,
    decisao         text,                   -- sql | sem_dados | esclarecimento | conversa
    sql_final       text,
    sqls_tentados   jsonb,
    tentativas      int,
    sucesso         boolean,
    erro            text,
    mensagem        text,
    suposicoes      jsonb,
    colunas         jsonb,
    linhas          jsonb,
    n_linhas        int,
    truncado        boolean,
    narrativa       text,
    modelo          text,
    esforco         text,
    config_hash     text,
    tokens_entrada  int,
    tokens_saida    int,
    custo_usd       numeric(12, 6),
    tempo_total_ms  int,
    etapas          jsonb
);
create index if not exists execucoes_rodada_idx on indaga.execucoes (rodada, pergunta_id);

-- O schema indaga não é exposto pela API REST do Supabase; ainda assim,
-- garante que os papéis públicos não o enxerguem.
revoke all on schema indaga from anon, authenticated;
revoke all on schema olist from anon, authenticated;

-- ── Usuário somente leitura ──────────────────────────────────────────────
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'indaga_leitor') then
        create role indaga_leitor with login password 'TROQUE_ESTA_SENHA';
    end if;
end $$;

grant usage on schema olist to indaga_leitor;
grant select on all tables in schema olist to indaga_leitor;
-- Tabelas criadas depois (pelo script de carga) já nascem legíveis.
alter default privileges in schema olist grant select on tables to indaga_leitor;

alter role indaga_leitor set default_transaction_read_only = on;
alter role indaga_leitor set statement_timeout = '20s';
alter role indaga_leitor set search_path = olist;
