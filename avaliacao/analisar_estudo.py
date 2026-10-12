"""Corrige e resume o estudo com usuários (Fase 6).

Uso:
    python avaliacao/analisar_estudo.py              participantes reais (P...)
    python avaliacao/analisar_estudo.py --piloto     só o piloto (T...)

Gera, em avaliacao/resultados/:
    estudo_respostas.csv      uma linha por resposta, com a correção e, no
                              Indaga, o que a IA respondeu e o viés de automação
    estudo_resumo.csv         ferramenta x tipo de pergunta: acerto, tempo, confiança
    estudo_pareado.csv        uma linha por participante, as duas ferramentas lado
                              a lado (entrada para o teste de Wilcoxon pareado)
    estudo_participantes.csv  perfil, grupo, preferências e comentários

Correção da resposta do participante (definida antes da coleta):
    numero/percentual  o primeiro número escrito na resposta, dentro da maior
                       entre a tolerância do gabarito e 0,5% do valor. Os 0,5%
                       aceitam a leitura abreviada dos cartões ("6,11 Mi").
                       Em percentual, aceita pontos (6,6) ou fração (0,066).
    lista              o mesmo conjunto de itens, sem acento, maiúsculas,
                       espaços ou sublinhados; a ordem não conta
    recusa             correto se marcou "os dados não permitem responder"
    rubrica            pendente_manual
"não consegui encontrar" vira nao_respondeu e não conta como erro nem acerto.

Viés de automação: no Indaga, a última resposta da IA estava errada, o
participante respondeu errado e declarou confiança 4 ou 5.
"""
import argparse
import csv
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent))
sys.path.insert(0, str(PASTA))

from indaga import banco  # noqa: E402
import corrigir  # noqa: E402

_NUM = re.compile(r"(\d[\d.,]*)\s*(milh\w*|mi\b|mil\b|bilh\w*|bi\b|k\b)?", re.IGNORECASE)
# Ordem importa: "mil" antes de "mi", senão "53,53 mil" vira milhões.
_ESCALA = [("milh", 1e6), ("mil", 1e3), ("mi", 1e6), ("k", 1e3), ("bilh", 1e9), ("bi", 1e9)]


def numero_do_texto(texto: str | None) -> float | None:
    """Primeiro número de uma resposta escrita em português ("R$ 6,11 Mi", "53.532", "4.09")."""
    if not texto:
        return None
    m = _NUM.search(texto)
    if not m:
        return None
    bruto, sufixo = m.group(1).rstrip(".,"), (m.group(2) or "").lower()
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif bruto.count(".") >= 1 and all(len(g) == 3 for g in bruto.split(".")[1:]):
        bruto = bruto.replace(".", "")  # 53.532 = cinquenta e três mil
    try:
        valor = float(bruto)
    except ValueError:
        return None
    escala = next((f for k, f in _ESCALA if sufixo.startswith(k)), 1)
    return valor * escala


def _normal(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[\s_\-]+", "", s)


def corrigir_participante(resp: dict, pergunta: dict, gabarito) -> str:
    criterio, situacao = pergunta["criterio"], resp["situacao"]
    if situacao == "nao_consegui":
        return "nao_respondeu"
    if criterio == "recusa":
        return "correto" if situacao == "sem_dados" else "incorreto"
    if criterio == "rubrica":
        return "pendente_manual"
    if situacao == "sem_dados":
        return "incorreto"  # a base tem o dado
    _, gab = gabarito
    if criterio in ("numero", "percentual"):
        alvo, valor = corrigir._num(gab[0][0]), numero_do_texto(resp["resposta"])
        if alvo is None or valor is None:
            return "incorreto"
        tol = max(float(pergunta["tolerancia"] or 0.01), 0.005 * abs(alvo))
        escalas = (1, 100) if criterio == "percentual" else (1,)
        return "correto" if any(abs(valor * e - alvo) <= tol for e in escalas) else "incorreto"
    if criterio == "lista":
        itens = {_normal(x) for x in re.split(r"[,;\n]|\be\b", resp["resposta"] or "") if x.strip()}
        return "correto" if itens == {_normal(l[0]) for l in gab} else "incorreto"
    return f"criterio_desconhecido:{criterio}"


def _ler(cur, sql, params=()):
    cur.execute(sql, params)
    nomes = [d[0] for d in cur.description]
    return [dict(zip(nomes, l)) for l in cur.fetchall()]


def _mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else ""


def _media(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 2) if xs else ""


def _pct(n, d):
    return round(100 * n / d, 1) if d else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--piloto", action="store_true", help="analisa só os participantes do piloto")
    args = parser.parse_args()

    with (PASTA / "perguntas.csv").open(encoding="utf-8", newline="") as f:
        perguntas = {p["id"]: p for p in csv.DictReader(f)}

    with banco.conexao_admin() as conn, conn.cursor() as cur:
        participantes = _ler(cur, "SELECT * FROM indaga.estudo_participantes WHERE piloto = %s ORDER BY id", (args.piloto,))
        ids = [p["id"] for p in participantes] or [-1]
        respostas = _ler(cur, "SELECT * FROM indaga.estudo_respostas WHERE participante_id = ANY(%s) ORDER BY participante_id, bloco, posicao", (ids,))
        sus = _ler(cur, "SELECT * FROM indaga.estudo_sus WHERE participante_id = ANY(%s)", (ids,))
        eventos = _ler(cur, "SELECT * FROM indaga.estudo_eventos WHERE participante_id = ANY(%s)", (ids,))
        codigos = [p["codigo"] for p in participantes]
        execucoes = _ler(cur, "SELECT id, participante, pergunta_id, decisao, sucesso, linhas FROM indaga.execucoes "
                              "WHERE origem = 'estudo' AND participante = ANY(%s) ORDER BY id", (codigos,))

    if not participantes:
        sys.exit("Nenhum participante encontrado.")
    por_id = {p["id"]: p for p in participantes}
    gabaritos = {}
    for pid in {r["pergunta_id"] for r in respostas}:
        p = perguntas[pid]
        if p["criterio"] in ("numero", "percentual", "lista") and p["gabarito_sql"].strip():
            gabaritos[pid] = banco.executar_leitura(p["gabarito_sql"])[:2]
    execs = defaultdict(list)
    for e in execucoes:
        execs[(e["participante"], e["pergunta_id"])].append(e)
    abriu_sql = {(e["participante_id"], e["pergunta_id"]) for e in eventos if e["tipo"] == "abriu_sql"}

    saida = PASTA / "resultados"
    saida.mkdir(exist_ok=True)
    linhas = []
    for r in respostas:
        part, perg = por_id[r["participante_id"]], perguntas[r["pergunta_id"]]
        linha = {
            "participante": part["codigo"], "grupo": part["grupo"], "pergunta_id": r["pergunta_id"],
            "tipo": perg["tipo"], "criterio": perg["criterio"], "ferramenta": r["ferramenta"], "bloco": r["bloco"],
            "situacao": r["situacao"], "resposta": r["resposta"] or "", "confianca": r["confianca"],
            "conferiu": r["conferiu"], "tempo_s": round(r["tempo_ms"] / 1000, 1) if r["tempo_ms"] is not None else None,
            "correcao": corrigir_participante(r, perg, gabaritos.get(r["pergunta_id"])),
            "consultas_ia": "", "ia_ultima": "", "abriu_sql": "", "vies_automacao": "",
        }
        if r["ferramenta"] == "indaga":
            lista = execs[(part["codigo"], r["pergunta_id"])]
            linha["consultas_ia"] = len(lista)
            linha["abriu_sql"] = (r["participante_id"], r["pergunta_id"]) in abriu_sql
            if lista:
                linha["ia_ultima"] = corrigir.corrigir(lista[-1], perg, gabaritos.get(r["pergunta_id"]))
            linha["vies_automacao"] = (linha["ia_ultima"] == "incorreto" and linha["correcao"] == "incorreto"
                                       and (r["confianca"] or 0) >= 4)
        linhas.append(linha)

    with (saida / "estudo_respostas.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]) if linhas else ["participante"])
        w.writeheader()
        w.writerows(linhas)

    grupos = defaultdict(list)
    for l in linhas:
        grupos[(l["ferramenta"], l["tipo"])].append(l)
        grupos[(l["ferramenta"], "todos")].append(l)
    with (saida / "estudo_resumo.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ferramenta", "tipo", "respostas", "corretas_pct", "incorretas_pct", "nao_respondeu_pct",
                    "pendentes_manual", "tempo_mediano_s", "confianca_media", "conferiu_pct", "vies_automacao"])
        for (ferr, tipo), ls in sorted(grupos.items()):
            n = len(ls)
            cont = lambda c: sum(l["correcao"] == c for l in ls)
            respondidas = [l for l in ls if l["situacao"] == "respondida"]
            w.writerow([ferr, tipo, n, _pct(cont("correto"), n), _pct(cont("incorreto"), n), _pct(cont("nao_respondeu"), n),
                        cont("pendente_manual"), _mediana([l["tempo_s"] for l in ls]), _media([l["confianca"] for l in ls]),
                        _pct(sum(bool(l["conferiu"]) for l in respondidas), len(respondidas)),
                        sum(l["vies_automacao"] is True for l in ls)])

    notas = {(s["participante_id"], s["ferramenta"]): float(s["nota"]) for s in sus}
    with (saida / "estudo_pareado.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["participante", "acertos_dashboard", "acertos_indaga", "tempo_mediano_dashboard_s",
                    "tempo_mediano_indaga_s", "sus_dashboard", "sus_indaga"])
        for p in participantes:
            ls = [l for l in linhas if l["participante"] == p["codigo"]]
            de = lambda ferr: [l for l in ls if l["ferramenta"] == ferr]
            w.writerow([p["codigo"],
                        sum(l["correcao"] == "correto" for l in de("dashboard")),
                        sum(l["correcao"] == "correto" for l in de("indaga")),
                        _mediana([l["tempo_s"] for l in de("dashboard")]), _mediana([l["tempo_s"] for l in de("indaga")]),
                        notas.get((p["id"], "dashboard"), ""), notas.get((p["id"], "indaga"), "")])

    with (saida / "estudo_participantes.csv").open("w", encoding="utf-8", newline="") as f:
        campos_perfil = sorted({k for p in participantes for k in (p["perfil"] or {})})
        campos_pref = ["A", "B", "C", "D", "confiou_mais"]
        w = csv.writer(f)
        w.writerow(["participante", "grupo", "concluido", *campos_perfil, *[f"pref_{c}" for c in campos_pref], "comentarios"])
        for p in participantes:
            pref = p["preferencias"] or {}
            w.writerow([p["codigo"], p["grupo"], p["concluido_em"] is not None,
                        *[(p["perfil"] or {}).get(c, "") for c in campos_perfil],
                        *[pref.get(c, "") for c in campos_pref], p["comentarios"] or ""])

    concluidos = sum(p["concluido_em"] is not None for p in participantes)
    print(f"Participantes: {len(participantes)} ({concluidos} concluíram)")
    for ferr in ("dashboard", "indaga"):
        ls = [l for l in linhas if l["ferramenta"] == ferr]
        nts = [v for (_, f_), v in notas.items() if f_ == ferr]
        print(f"  {ferr:<10} respostas {len(ls):>3}  corretas {_pct(sum(l['correcao'] == 'correto' for l in ls), len(ls))}%  "
              f"tempo mediano {_mediana([l['tempo_s'] for l in ls])} s  SUS médio {_media(nts)}")
    vies = sum(l["vies_automacao"] is True for l in linhas)
    print(f"  Viés de automação (IA errada aceita com confiança 4 ou 5): {vies}")
    pend = sum(l["correcao"] == "pendente_manual" for l in linhas)
    if pend:
        print(f"  {pend} respostas com rubrica aguardam correção manual em estudo_respostas.csv.")
    print(f"Arquivos em {saida}")


if __name__ == "__main__":
    main()
