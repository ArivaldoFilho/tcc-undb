"""Grava cada execução na tabela indaga.execucoes."""
import json

from psycopg2.extras import Json

from . import banco

_SQL = """
INSERT INTO indaga.execucoes (
    origem, rodada, pergunta_id, repeticao, participante,
    pergunta, decisao, sql_final, sqls_tentados, tentativas, sucesso, erro,
    mensagem, suposicoes, colunas, linhas, n_linhas, truncado, narrativa,
    modelo, esforco, config_hash, tokens_entrada, tokens_saida, custo_usd,
    tempo_total_ms, etapas
) VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s
) RETURNING id
"""


def gravar(r: dict, *, origem, rodada, pergunta_id, repeticao, participante) -> int:
    m = r["metricas"]
    valores = (
        origem, rodada, pergunta_id, repeticao, participante,
        r["pergunta"], r["decisao"], r["sql"], Json(r["sqls_tentados"]), r["tentativas"], r["sucesso"], r["erro"],
        r["mensagem"], Json(r["suposicoes"]), Json(r["colunas"]), Json(r["linhas"]), r["n_linhas"], r["truncado"], r["narrativa"],
        m["modelo"], m["esforco"], m["config_hash"], m["tokens_entrada"], m["tokens_saida"], m["custo_usd"],
        m["tempo_total_ms"], Json(m["etapas"]),
    )
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL, valores)
            novo_id = cur.fetchone()[0]
        conn.commit()
    return novo_id


def para_json(r: dict) -> str:
    return json.dumps(r, ensure_ascii=False, default=str)


def consultas_24h(origem: str) -> int:
    """Execuções gravadas nas últimas 24 horas para uma origem (teto da interface pública)."""
    with banco.conexao_admin() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM indaga.execucoes WHERE origem = %s AND criado_em > now() - interval '24 hours'",
            (origem,),
        )
        return cur.fetchone()[0]
