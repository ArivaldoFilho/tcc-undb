-- Indaga: tabelas do estudo com usuários (Fase 6).
-- Rodar com o DATABASE_URL (usuário indaga_app, dono do schema indaga):
--     .venv\Scripts\python scripts\criar_estudo.py
--
-- Nenhum dado pessoal identificável é gravado: o participante é um código
-- (P001...) e o perfil tem só faixas de experiência.

create table if not exists indaga.estudo_participantes (
    id                bigserial primary key,
    codigo            text unique,               -- P001 (real) ou T001 (piloto)
    token             text unique not null,      -- identifica a sessão no navegador
    grupo             int not null,              -- 0 a 3: ordem das ferramentas x conjunto de perguntas
    piloto            boolean not null default false,
    criado_em         timestamptz not null default now(),
    consentimento_em  timestamptz not null,
    perfil            jsonb not null,
    preferencias      jsonb,
    comentarios       text,
    concluido_em      timestamptz,
    navegador         text
);

create table if not exists indaga.estudo_respostas (
    id              bigserial primary key,
    participante_id bigint not null references indaga.estudo_participantes (id),
    pergunta_id     text not null,
    ferramenta      text not null check (ferramenta in ('dashboard', 'indaga')),
    bloco           int not null,                -- 1 = primeira ferramenta, 2 = segunda
    posicao         int not null,                -- ordem da pergunta dentro do bloco
    situacao        text not null check (situacao in ('respondida', 'sem_dados', 'nao_consegui')),
    resposta        text,
    confianca       int check (confianca between 1 and 5),
    conferiu        boolean,
    tempo_ms        int,                         -- da ferramenta carregada ao envio
    tempo_total_ms  int,                         -- da tela aberta ao envio
    enviado_em      timestamptz not null default now(),
    unique (participante_id, pergunta_id)
);

create table if not exists indaga.estudo_sus (
    participante_id bigint not null references indaga.estudo_participantes (id),
    ferramenta      text not null check (ferramenta in ('dashboard', 'indaga')),
    itens           jsonb not null,              -- 10 respostas de 1 a 5, na ordem do questionário
    nota            numeric(5, 1) not null,      -- 0 a 100
    enviado_em      timestamptz not null default now(),
    primary key (participante_id, ferramenta)
);

create table if not exists indaga.estudo_eventos (
    id              bigserial primary key,
    participante_id bigint not null references indaga.estudo_participantes (id),
    pergunta_id     text,
    tipo            text not null,               -- abriu_sql
    execucao_id     bigint,
    criado_em       timestamptz not null default now()
);

create index if not exists execucoes_participante_idx on indaga.execucoes (participante, pergunta_id);
