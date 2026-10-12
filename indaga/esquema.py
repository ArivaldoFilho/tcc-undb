"""Monta o texto do esquema enviado ao modelo.

Os nomes e tipos das colunas vêm do próprio banco (information_schema). As
descrições, relacionamentos e definições de métricas vêm de
config/descricoes.json, que faz o papel da camada semântica: é o mesmo
conjunto de definições que as medidas do dashboard precisam seguir.

Nenhuma linha de dados é enviada nesta etapa, só a estrutura e as descrições.
"""
import json
from functools import lru_cache

from . import banco, config


def carregar_descricoes() -> dict:
    return json.loads(config.ARQUIVO_DESCRICOES.read_text(encoding="utf-8"))


def _colunas_do_banco() -> dict[str, list[tuple[str, str]]]:
    sql = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
    """
    tabelas: dict[str, list[tuple[str, str]]] = {}
    with banco.conexao_admin() as conn, conn.cursor() as cur:
        cur.execute(sql, (config.ESQUEMA_DADOS,))
        for tabela, coluna, tipo in cur.fetchall():
            tabelas.setdefault(tabela, []).append((coluna, tipo))
    return tabelas


def avisos_de_divergencia(colunas: dict, descricoes: dict) -> list[str]:
    """Colunas descritas que não existem no banco, e vice-versa."""
    avisos = []
    desc_tabelas = descricoes.get("tabelas", {})
    for tabela, cols in colunas.items():
        desc_cols = desc_tabelas.get(tabela, {}).get("colunas", {})
        if tabela not in desc_tabelas:
            avisos.append(f"Tabela sem descrição: {tabela}")
        for nome, _ in cols:
            if nome not in desc_cols:
                avisos.append(f"Coluna sem descrição: {tabela}.{nome}")
        for nome in desc_cols:
            if nome not in {c for c, _ in cols}:
                avisos.append(f"Coluna descrita mas inexistente no banco: {tabela}.{nome}")
    for tabela in desc_tabelas:
        if tabela not in colunas:
            avisos.append(f"Tabela descrita mas inexistente no banco: {tabela}")
    return avisos


@lru_cache(maxsize=1)
def texto_do_esquema() -> str:
    colunas = _colunas_do_banco()
    if not colunas:
        raise RuntimeError(
            f"Nenhuma tabela encontrada no schema '{config.ESQUEMA_DADOS}'. "
            "Rode scripts/carregar_olist.py antes de iniciar."
        )
    descricoes = carregar_descricoes()
    desc_tabelas = descricoes.get("tabelas", {})
    s = config.ESQUEMA_DADOS
    partes = [f"Banco PostgreSQL. Todas as tabelas estão no schema {s}."]

    for tabela, cols in colunas.items():
        desc = desc_tabelas.get(tabela, {})
        partes.append(f"\nTabela {s}.{tabela}: {desc.get('descricao', '')}".rstrip(": "))
        desc_cols = desc.get("colunas", {})
        for nome, tipo in cols:
            linha = f"  - {nome} ({tipo})"
            if desc_cols.get(nome):
                linha += f": {desc_cols[nome]}"
            partes.append(linha)

    if descricoes.get("relacionamentos"):
        partes.append("\nRelacionamentos (junções válidas):")
        partes.extend(f"  - {r}" for r in descricoes["relacionamentos"])
    if descricoes.get("definicoes"):
        partes.append("\nDefinições de negócio (use sempre estas, salvo pedido explícito em contrário):")
        partes.extend(f"  - {d}" for d in descricoes["definicoes"])
    if descricoes.get("observacoes"):
        partes.append("\nObservações sobre a qualidade dos dados:")
        partes.extend(f"  - {o}" for o in descricoes["observacoes"])
    return "\n".join(partes)
