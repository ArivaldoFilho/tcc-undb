"""Conexões com o PostgreSQL e execução segura do SQL gerado."""
import datetime as dt
import decimal
import re
from contextlib import contextmanager

import psycopg2

from . import config


@contextmanager
def conexao_admin():
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada no .env")
    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def conexao_leitura():
    url = config.DATABASE_URL_LEITURA or config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL_LEITURA não configurada no .env")
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


# ── Guardrail ────────────────────────────────────────────────────────────
_PROIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|"
    r"COPY|CALL|DO|EXECUTE|VACUUM|ANALYZE|REINDEX|CLUSTER|LOCK|SET|RESET|"
    r"LISTEN|NOTIFY|PREPARE|DEALLOCATE|COMMENT|SECURITY|REFRESH)\b",
    re.IGNORECASE,
)
_LITERAIS_E_COMENTARIOS = re.compile(r"'(?:[^']|'')*'|\"[^\"]*\"|--[^\n]*|/\*.*?\*/", re.DOTALL)


def violacao_guardrail(sql: str) -> str | None:
    """Primeira das três barreiras (as outras são a transação somente leitura e
    o usuário sem permissão de escrita). Retorna o motivo do bloqueio ou None."""
    texto = (sql or "").strip().rstrip(";").strip()
    if not texto:
        return "SQL vazio."
    # Palavras dentro de strings e comentários não contam ('Delete' num filtro é legítimo).
    sem_literais = _LITERAIS_E_COMENTARIOS.sub(" ", texto)
    if ";" in sem_literais:
        return "Mais de um comando na mesma consulta."
    if not re.match(r"^\s*(SELECT|WITH)\b", sem_literais, re.IGNORECASE):
        return "A consulta precisa começar com SELECT ou WITH."
    proibida = _PROIBIDAS.search(sem_literais)
    if proibida:
        return f"Comando não permitido: {proibida.group(1).upper()}."
    return None


def _valor_json(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, dt.timedelta):
        return v.total_seconds()
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def executar_leitura(sql: str) -> tuple[list[str], list[list], bool]:
    """Executa em transação somente leitura, com timeout, e sempre faz rollback."""
    with conexao_leitura() as conn:
        conn.set_session(readonly=True, autocommit=False)
        try:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL statement_timeout = '{config.TIMEOUT_SQL_SEGUNDOS}s'")
                cur.execute(sql.strip().rstrip(";"))
                colunas = [d[0] for d in cur.description] if cur.description else []
                brutas = cur.fetchmany(config.MAX_LINHAS + 1)
        finally:
            conn.rollback()
    truncado = len(brutas) > config.MAX_LINHAS
    linhas = [[_valor_json(v) for v in linha] for linha in brutas[: config.MAX_LINHAS]]
    return colunas, linhas, truncado
