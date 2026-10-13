"""Matriz de decisão por tipo de pergunta (Frente D).

Uso:
    python avaliacao/matriz.py --rodada final
    python avaliacao/matriz.py --rodada participantes --arquivo avaliacao/perguntas_participantes.csv \
        --painel avaliacao/dashboard_participantes.csv

Junta o <rodada>_resumo.csv (Indaga, depois da revisão manual) com a ficha do
painel e gera avaliacao/resultados/matriz_<rodada>.csv. Linhas:

    uma por tipo (A, B, C, D), com cobertura "todas";
    uma por valor de coberta_pela_documentacao (sim, nao), com tipo "todos";
    o total ("todos", "todas").

coberta_pela_documentacao (coluna do arquivo de perguntas) diz se tudo o que
a pergunta exige está escrito em config/descricoes.json. Separar por ela mostra
quanto do acerto da IA vem da documentação e quanto do raciocínio do modelo.
Perguntas sem a coluna preenchida ficam como "sem_classificacao".

Colunas:

    Indaga  acerto (corretas sobre julgadas, somando as perguntas do tipo),
            consistência média, tempo mediano, custo médio, perguntas com
            pendência de revisão
    Painel  cobertura (sim / parcial / não), passos médios quando responde,
            esforço de adaptação médio quando não responde (escala 0 a 3)
"""
import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

PASTA = Path(__file__).resolve().parent


def _ler(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _media(xs, casas=1):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), casas) if xs else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rodada", required=True)
    parser.add_argument("--arquivo", type=Path, default=PASTA / "perguntas.csv")
    parser.add_argument("--painel", type=Path, default=PASTA / "dashboard.csv")
    args = parser.parse_args()

    perguntas = {p["id"]: p for p in _ler(args.arquivo)}
    resumo = _ler(PASTA / "resultados" / f"{args.rodada}_resumo.csv")
    painel = {l["id"]: l for l in _ler(args.painel)}

    grupos = defaultdict(list)
    for r in resumo:
        p = perguntas[r["pergunta_id"]]
        cobertura = (p.get("coberta_pela_documentacao") or "").strip().lower() or "sem_classificacao"
        grupos[(p["tipo"], "todas")].append(r)
        grupos[("todos", cobertura)].append(r)
        grupos[("todos", "todas")].append(r)

    ordem = [(t, "todas") for t in "ABCD"] + [("todos", c) for c in ("sim", "nao", "sem_classificacao")]
    linhas = []
    for tipo, cobertura in [g for g in ordem if g in grupos] + [("todos", "todas")]:
        rs = grupos[(tipo, cobertura)]
        corretas = sum(int(r["corretas"]) for r in rs)
        julgadas = sum(int(r["corretas"]) + int(r["incorretas"]) for r in rs)
        fichas = [painel.get(r["pergunta_id"], {}) for r in rs]
        resp = [(f.get("responde") or "").strip().lower() for f in fichas]
        linhas.append({
            "tipo": tipo, "coberta_pela_documentacao": cobertura, "perguntas": len(rs),
            "ia_acerto_pct": round(100 * corretas / julgadas, 1) if julgadas else "",
            "ia_consistencia_pct": _media([_f(r["consistencia_resultado_pct"]) for r in rs]),
            "ia_tempo_mediano_s": round(statistics.median([_f(r["tempo_mediano_s"]) for r in rs]), 1),
            "ia_custo_medio_usd": _media([_f(r["custo_medio_usd"]) for r in rs], 4),
            "ia_pendentes_revisao": sum(int(r["pendentes_manual"]) > 0 for r in rs),
            "painel_sim": resp.count("sim"), "painel_parcial": resp.count("parcial"), "painel_nao": resp.count("nao"),
            "painel_sem_ficha": resp.count(""),
            "painel_passos_medios": _media([_f(f.get("passos")) for f, x in zip(fichas, resp) if x == "sim"]),
            "painel_esforco_adaptacao_medio": _media([_f(f.get("esforco_adaptacao")) for f, x in zip(fichas, resp)
                                                     if x in ("nao", "parcial")]),
        })

    saida = PASTA / "resultados" / f"matriz_{args.rodada}.csv"
    with saida.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    cab = list(linhas[0])
    print("| " + " | ".join(cab) + " |")
    print("|" + "---|" * len(cab))
    for l in linhas:
        print("| " + " | ".join(str(l[c]) for c in cab) + " |")
    print(f"\nGravado em {saida}")
    if any(l["painel_sem_ficha"] for l in linhas):
        print("Atenção: há perguntas sem a coluna 'responde' preenchida na ficha do painel.")


if __name__ == "__main__":
    main()
