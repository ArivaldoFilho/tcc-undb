"""Estudo com usuários (Fase 6): participantes, plano de perguntas e respostas.

Desenho intrassujeito com contrabalanceamento. Cada participante usa as duas
ferramentas, cada uma com um conjunto diferente e equivalente de perguntas.
Os quatro grupos cruzam a ordem das ferramentas com o conjunto de perguntas:

    grupo 0: dashboard com X, depois indaga com Y
    grupo 1: indaga com X, depois dashboard com Y
    grupo 2: dashboard com Y, depois indaga com X
    grupo 3: indaga com Y, depois dashboard com X

O grupo é atribuído ao menos preenchido no momento da entrada, para que os
quatro fiquem equilibrados mesmo com desistências.
"""
import csv
import json
import secrets
from functools import lru_cache

from psycopg2.extras import Json

from . import banco, config

GRUPOS = [
    [("dashboard", "X"), ("indaga", "Y")],
    [("indaga", "X"), ("dashboard", "Y")],
    [("dashboard", "Y"), ("indaga", "X")],
    [("indaga", "Y"), ("dashboard", "X")],
]
FERRAMENTAS = ("dashboard", "indaga")
SITUACOES = ("respondida", "sem_dados", "nao_consegui")


class ErroEstudo(Exception):
    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.status = status


@lru_cache
def configuracao() -> dict:
    return json.loads((config.RAIZ / "config" / "estudo.json").read_text(encoding="utf-8"))


@lru_cache
def perguntas() -> dict[str, dict]:
    with (config.RAIZ / "avaliacao" / "perguntas.csv").open(encoding="utf-8", newline="") as f:
        return {p["id"]: p for p in csv.DictReader(f)}


def plano(grupo: int) -> list[dict]:
    todas = perguntas()
    conjuntos = configuracao()["conjuntos"]
    return [
        {"bloco": i, "ferramenta": ferramenta, "conjunto": conjunto,
         "perguntas": [{"id": pid, "tipo": todas[pid]["tipo"], "texto": todas[pid]["pergunta"]}
                       for pid in conjuntos[conjunto]]}
        for i, (ferramenta, conjunto) in enumerate(GRUPOS[grupo], start=1)
    ]


def _participante(cur, token: str) -> dict:
    cur.execute(
        "SELECT id, codigo, grupo, piloto, concluido_em FROM indaga.estudo_participantes WHERE token = %s",
        (token or "",),
    )
    linha = cur.fetchone()
    if not linha:
        raise ErroEstudo("Sessão do estudo não encontrada. Abra o link do estudo novamente.", 401)
    return dict(zip(("id", "codigo", "grupo", "piloto", "concluido_em"), linha))


def iniciar(perfil: dict, piloto: bool, navegador: str | None) -> dict:
    token = secrets.token_urlsafe(24)
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            # Serializa as entradas simultâneas para o sorteio do grupo não empatar.
            cur.execute("SELECT pg_advisory_xact_lock(hashtext('indaga_estudo'))")
            cur.execute(
                "SELECT grupo, count(*) FROM indaga.estudo_participantes WHERE piloto = %s GROUP BY grupo",
                (piloto,),
            )
            contagem = dict(cur.fetchall())
            grupo = min(range(len(GRUPOS)), key=lambda g: (contagem.get(g, 0), g))
            cur.execute(
                "INSERT INTO indaga.estudo_participantes (token, grupo, piloto, consentimento_em, perfil, navegador) "
                "VALUES (%s, %s, %s, now(), %s, %s) RETURNING id",
                (token, grupo, piloto, Json(perfil), (navegador or "")[:300]),
            )
            pid = cur.fetchone()[0]
            cur.execute(
                "SELECT count(*) FROM indaga.estudo_participantes WHERE piloto = %s AND id <= %s", (piloto, pid)
            )
            codigo = f"{'T' if piloto else 'P'}{cur.fetchone()[0]:03d}"
            cur.execute("UPDATE indaga.estudo_participantes SET codigo = %s WHERE id = %s", (codigo, pid))
        conn.commit()
    return {"token": token, **estado(token)}


def estado(token: str) -> dict:
    with banco.conexao_admin() as conn, conn.cursor() as cur:
        p = _participante(cur, token)
        cur.execute("SELECT pergunta_id FROM indaga.estudo_respostas WHERE participante_id = %s", (p["id"],))
        respondidas = [r for (r,) in cur.fetchall()]
        cur.execute("SELECT ferramenta FROM indaga.estudo_sus WHERE participante_id = %s", (p["id"],))
        sus = [r for (r,) in cur.fetchall()]
    return {
        "codigo": p["codigo"], "piloto": p["piloto"], "plano": plano(p["grupo"]),
        "respondidas": respondidas, "sus": sus, "concluido": p["concluido_em"] is not None,
        "dashboard_url": configuracao()["dashboard_url"],
    }


def _localizar(plano_: list[dict], pergunta_id: str) -> tuple[dict, int]:
    for bloco in plano_:
        for posicao, perg in enumerate(bloco["perguntas"], start=1):
            if perg["id"] == pergunta_id:
                return bloco, posicao
    raise ErroEstudo("Pergunta fora do plano deste participante.")


def responder(token: str, dados: dict) -> None:
    situacao = dados.get("situacao")
    if situacao not in SITUACOES:
        raise ErroEstudo("Situação inválida.")
    resposta = (dados.get("resposta") or "").strip()[:2000] or None
    if situacao == "respondida" and not resposta:
        raise ErroEstudo("Escreva a resposta encontrada.")
    confianca = dados.get("confianca")
    if situacao != "nao_consegui" and confianca not in (1, 2, 3, 4, 5):
        raise ErroEstudo("Informe a confiança, de 1 a 5.")
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            p = _participante(cur, token)
            bloco, posicao = _localizar(plano(p["grupo"]), dados.get("pergunta_id"))
            cur.execute(
                "INSERT INTO indaga.estudo_respostas (participante_id, pergunta_id, ferramenta, bloco, posicao, "
                "situacao, resposta, confianca, conferiu, tempo_ms, tempo_total_ms) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (participante_id, pergunta_id) DO NOTHING",
                (p["id"], dados["pergunta_id"], bloco["ferramenta"], bloco["bloco"], posicao, situacao, resposta,
                 confianca if situacao != "nao_consegui" else None,
                 dados.get("conferiu") if situacao == "respondida" else None,
                 _inteiro(dados.get("tempo_ms")), _inteiro(dados.get("tempo_total_ms"))),
            )
        conn.commit()


def _inteiro(v) -> int | None:
    try:
        return max(0, min(int(v), 24 * 3600 * 1000))
    except (TypeError, ValueError):
        return None


def nota_sus(itens: list[int]) -> float:
    """Pontuação padrão do SUS: itens ímpares valem (x - 1), pares (5 - x); soma x 2,5."""
    return sum((x - 1) if i % 2 == 0 else (5 - x) for i, x in enumerate(itens)) * 2.5


def registrar_sus(token: str, ferramenta: str, itens: list) -> None:
    if ferramenta not in FERRAMENTAS:
        raise ErroEstudo("Ferramenta inválida.")
    if len(itens) != 10 or any(x not in (1, 2, 3, 4, 5) for x in itens):
        raise ErroEstudo("Responda os 10 itens, de 1 a 5.")
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            p = _participante(cur, token)
            cur.execute(
                "INSERT INTO indaga.estudo_sus (participante_id, ferramenta, itens, nota) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (participante_id, ferramenta) DO NOTHING",
                (p["id"], ferramenta, Json(itens), nota_sus(itens)),
            )
        conn.commit()


def concluir(token: str, preferencias: dict, comentarios: str | None) -> None:
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            p = _participante(cur, token)
            cur.execute(
                "UPDATE indaga.estudo_participantes SET preferencias = %s, comentarios = %s, concluido_em = now() "
                "WHERE id = %s AND concluido_em IS NULL",
                (Json(preferencias), (comentarios or "").strip()[:4000] or None, p["id"]),
            )
        conn.commit()


def registrar_evento(token: str, pergunta_id: str | None, tipo: str, execucao_id: int | None) -> None:
    if tipo not in ("abriu_sql",):
        raise ErroEstudo("Evento inválido.")
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            p = _participante(cur, token)
            cur.execute(
                "INSERT INTO indaga.estudo_eventos (participante_id, pergunta_id, tipo, execucao_id) "
                "VALUES (%s, %s, %s, %s)",
                (p["id"], pergunta_id, tipo, execucao_id),
            )
        conn.commit()


def autorizar_consulta_ia(token: str, pergunta_id: str | None) -> tuple[str, str]:
    """Valida uma pergunta ao Indaga feita dentro do estudo. Devolve (código, rodada).

    Só aceita perguntas do bloco do Indaga ainda não respondidas, com um teto de
    consultas por pergunta para limitar o custo de um link público."""
    with banco.conexao_admin() as conn, conn.cursor() as cur:
        p = _participante(cur, token)
        if p["concluido_em"]:
            raise ErroEstudo("Este participante já concluiu o estudo.", 403)
        bloco, _ = _localizar(plano(p["grupo"]), pergunta_id)
        if bloco["ferramenta"] != "indaga":
            raise ErroEstudo("Esta pergunta deve ser respondida no painel.", 403)
        cur.execute(
            "SELECT 1 FROM indaga.estudo_respostas WHERE participante_id = %s AND pergunta_id = %s",
            (p["id"], pergunta_id),
        )
        if cur.fetchone():
            raise ErroEstudo("Esta pergunta já foi respondida.", 403)
        cur.execute(
            "SELECT count(*) FROM indaga.execucoes WHERE origem = 'estudo' AND participante = %s AND pergunta_id = %s",
            (p["codigo"], pergunta_id),
        )
        if cur.fetchone()[0] >= configuracao()["max_consultas_ia_por_pergunta"]:
            raise ErroEstudo("Limite de consultas para esta pergunta atingido. Responda com o que encontrou.", 429)
    return p["codigo"], "estudo_piloto" if p["piloto"] else "estudo"
