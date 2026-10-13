"""Concordância entre dois julgadores: percentual e kappa de Cohen.

Uso:
    python avaliacao/concordancia.py avaliacao/resultados/final_revisao.csv
    python avaliacao/concordancia.py classificacao.csv --colunas tipo_autor tipo_segundo

Serve para os julgamentos de recusa e rubrica (A5: colunas avaliador_1 e
avaliador_2 do <rodada>_revisao.csv) e para a classificação das perguntas dos
participantes nos tipos A a D (C3). Só entram as linhas com os dois campos
preenchidos. As divergências são listadas para a resolução por consenso.
"""
import argparse
import csv
from collections import Counter
from pathlib import Path


def kappa(pares: list[tuple[str, str]]) -> float | None:
    n = len(pares)
    if not n:
        return None
    observada = sum(a == b for a, b in pares) / n
    ca, cb = Counter(a for a, _ in pares), Counter(b for _, b in pares)
    esperada = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if esperada == 1 else (observada - esperada) / (1 - esperada)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("arquivo", type=Path)
    parser.add_argument("--colunas", nargs=2, default=["avaliador_1", "avaliador_2"], metavar=("A", "B"))
    args = parser.parse_args()

    with args.arquivo.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    a, b = args.colunas
    norm = lambda v: (v or "").strip().lower()
    julgadas = [l for l in linhas if norm(l.get(a)) and norm(l.get(b))]
    pares = [(norm(l[a]), norm(l[b])) for l in julgadas]
    if not pares:
        raise SystemExit(f"Nenhuma linha com '{a}' e '{b}' preenchidos.")
    iguais = sum(x == y for x, y in pares)
    print(f"Linhas julgadas pelos dois: {len(pares)} de {len(linhas)}")
    print(f"Concordância: {iguais}/{len(pares)} = {100 * iguais / len(pares):.1f}%")
    print(f"Kappa de Cohen: {kappa(pares):.3f}")
    divergentes = [l for l in julgadas if norm(l[a]) != norm(l[b])]
    if divergentes:
        ident = next((c for c in ("chave", "id", "pergunta_id") if c in linhas[0]), list(linhas[0])[0])
        print("Divergências (resolver por consenso):")
        for l in divergentes:
            print(f"  {l[ident]}: {a}={l[a]} | {b}={l[b]}")


if __name__ == "__main__":
    main()
