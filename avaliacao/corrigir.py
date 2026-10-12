"""Corrige uma rodada contra o gabarito e calcula as métricas por pergunta.

Uso:
    python avaliacao/corrigir.py --rodada piloto

Gera, em avaliacao/resultados/:
    <rodada>_execucoes.csv   uma linha por execução, com a situação da correção
    <rodada>_resumo.csv      uma linha por pergunta: acerto, consistência, tempo, custo

Critérios (coluna "criterio" de perguntas.csv, definidos ANTES da coleta):
    numero   uma linha no resultado e alguma célula numérica igual ao gabarito,
             dentro da tolerância (absoluta, ou relativa se terminar em %)
    percentual  como numero, com o gabarito em pontos percentuais (8.11 = 8,11%);
             aceita a resposta em pontos (8.11) ou em fração (0.0811)
    lista    alguma coluna do resultado tem exatamente o mesmo conjunto de
             valores da primeira coluna do gabarito (a ordem não conta)
    tabela   mesmo multiconjunto de linhas (valores arredondados a 2 casas;
             a ordem das linhas e das colunas não conta)
    recusa   correto se a decisão foi sem_dados ou esclarecimento. Se a IA
             executou SQL e escreveu a explicação, fica "pendente_manual": a
             explicação pode avisar que falta o dado (ex.: "a base termina em
             2018"), o que também é correto, e só uma pessoa julga isso.
    rubrica  fica "pendente_manual" para correção humana

Também confere os números citados na narrativa: um número que não aparece no
resultado é marcado para revisão (possível alucinação na etapa de texto, mesmo
com o SQL certo).
"""
import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent))

from indaga import banco  # noqa: E402


def _num(v) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _norm(v) -> str:
    n = _num(v)
    if n is not None:
        return f"{round(n, 2):.2f}"
    return "" if v is None else str(v).strip().lower()


def _assinatura(linhas: list[list]) -> str:
    """Resultado normalizado, para medir se as repetições devolveram o mesmo."""
    chave = sorted(tuple(sorted(_norm(v) for v in linha)) for linha in linhas)
    return hashlib.md5(json.dumps(chave).encode()).hexdigest()[:10]


def _dentro(valor: float, alvo: float, tolerancia: str) -> bool:
    tol = (tolerancia or "0.01").strip()
    if tol.endswith("%"):
        return abs(valor - alvo) <= abs(alvo) * float(tol[:-1]) / 100
    return abs(valor - alvo) <= float(tol)


def corrigir(execucao: dict, pergunta: dict, gabarito: tuple[list, list] | None) -> str:
    criterio = pergunta["criterio"]
    decisao = execucao.get("decisao")
    if criterio == "recusa":
        if decisao in ("sem_dados", "esclarecimento"):
            return "correto"
        return "pendente_manual" if execucao.get("sucesso") and execucao.get("narrativa") else "incorreto"
    if not execucao.get("sucesso"):
        return "falha"
    if criterio == "rubrica":
        return "pendente_manual"
    if decisao != "sql":
        return "incorreto"
    if gabarito is None:
        return "sem_gabarito"
    linhas = execucao.get("linhas") or []
    _, gab = gabarito
    if criterio in ("numero", "percentual"):
        alvo = _num(gab[0][0]) if gab and gab[0] else None
        if alvo is None or len(linhas) != 1:
            return "incorreto"
        escalas = (1, 100) if criterio == "percentual" else (1,)
        return "correto" if any(
            _num(v) is not None and _dentro(_num(v) * e, alvo, pergunta["tolerancia"])
            for v in linhas[0] for e in escalas
        ) else "incorreto"
    if criterio == "lista":
        alvo = {_norm(l[0]) for l in gab}
        n_col = len(linhas[0]) if linhas else 0
        return "correto" if any({_norm(l[j]) for l in linhas} == alvo for j in range(n_col)) else "incorreto"
    if criterio == "tabela":
        return "correto" if _assinatura(linhas) == _assinatura(gab) else "incorreto"
    return f"criterio_desconhecido:{criterio}"


_NUMERO = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(%|mil\b|milh\w*|bilh\w*)?", re.IGNORECASE)
# Ordem importa: "milh" antes de "mil", senão "milhões" casa com "mil".
_ESCALA = {"milh": 1e6, "bilh": 1e9, "mil": 1e3}


def numeros_sem_correspondencia(narrativa: str | None, linhas: list[list]) -> list[str]:
    """Números citados na narrativa que não batem com nenhuma célula do resultado.
    Anos e inteiros pequenos (até 31) são ignorados: costumam ser datas ou contagens
    citadas na pergunta. A lista é só para revisão manual, não é veredito."""
    if not narrativa or not linhas:
        return []
    celulas = [_num(v) for linha in linhas for v in linha]
    celulas = [c for c in celulas if c is not None]
    suspeitos = []
    for m in _NUMERO.finditer(narrativa):
        inteiro, decimal, sufixo = m.group(1), m.group(2), (m.group(3) or "").lower()
        valor = float(inteiro.replace(".", "") + ("." + decimal if decimal else ""))
        escala = next((f for k, f in _ESCALA.items() if sufixo.startswith(k)), 1)
        valor *= escala
        if escala == 1 and not decimal and (valor <= 31 or 1990 <= valor <= 2100):
            continue
        tol = 0.01 * abs(valor) if escala > 1 else max(0.006, 0.0005 * abs(valor))
        if not any(abs(c - valor) <= tol for c in celulas):
            suspeitos.append(m.group(0).strip())
    return suspeitos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rodada", required=True)
    parser.add_argument("--arquivo", type=Path, default=PASTA / "perguntas.csv")
    args = parser.parse_args()

    entrada = PASTA / "resultados" / f"{args.rodada}.jsonl"
    if not entrada.exists():
        sys.exit(f"Não encontrei {entrada}")
    execucoes = [json.loads(l) for l in entrada.read_text(encoding="utf-8").splitlines() if l.strip()]
    with args.arquivo.open(encoding="utf-8", newline="") as f:
        perguntas = {p["id"]: p for p in csv.DictReader(f)}

    gabaritos = {}
    for pid in {e["pergunta_id"] for e in execucoes}:
        sql = perguntas[pid]["gabarito_sql"].strip()
        if sql and perguntas[pid]["criterio"] in ("numero", "percentual", "lista", "tabela"):
            gabaritos[pid] = banco.executar_leitura(sql)[:2]

    por_pergunta = defaultdict(list)
    saida_exec = PASTA / "resultados" / f"{args.rodada}_execucoes.csv"
    with saida_exec.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id_registro", "pergunta_id", "tipo", "repeticao", "decisao", "situacao",
                    "assinatura_resultado", "n_linhas", "tentativas", "tempo_s", "tokens_entrada",
                    "tokens_saida", "custo_usd", "numeros_narrativa_a_revisar", "erro", "sql"])
        for e in execucoes:
            p = perguntas[e["pergunta_id"]]
            situacao = corrigir(e, p, gabaritos.get(e["pergunta_id"]))
            assinatura = _assinatura(e.get("linhas") or []) if e.get("decisao") == "sql" and e.get("sucesso") else ""
            suspeitos = numeros_sem_correspondencia(e.get("narrativa"), e.get("linhas") or [])
            m = e["metricas"]
            por_pergunta[e["pergunta_id"]].append({**e, "situacao": situacao, "assinatura": assinatura})
            w.writerow([e.get("id"), e["pergunta_id"], p["tipo"], e["repeticao"], e.get("decisao"), situacao,
                        assinatura, e.get("n_linhas"), e.get("tentativas"), round(m["tempo_total_ms"] / 1000, 2),
                        m["tokens_entrada"], m["tokens_saida"], m["custo_usd"], "; ".join(suspeitos),
                        e.get("erro") or "", e.get("sql") or ""])

    saida_resumo = PASTA / "resultados" / f"{args.rodada}_resumo.csv"
    with saida_resumo.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pergunta_id", "tipo", "criterio", "execucoes", "corretas", "pendentes_manual", "taxa_acerto_pct",
                    "consistencia_resultado_pct", "sqls_distintos", "decisoes", "tempo_mediano_s",
                    "tempo_max_s", "custo_medio_usd"])
        for pid in sorted(por_pergunta):
            lista = por_pergunta[pid]
            p = perguntas[pid]
            n = len(lista)
            corretas = sum(x["situacao"] == "correto" for x in lista)
            pendentes = sum(x["situacao"] == "pendente_manual" for x in lista)
            corrigiveis = n - pendentes
            # Consistência: fração das execuções que caiu no resultado (ou na decisão) mais frequente.
            chaves = [x["assinatura"] or f"decisao:{x.get('decisao')}" for x in lista]
            consistencia = Counter(chaves).most_common(1)[0][1] / n
            tempos = [x["metricas"]["tempo_total_ms"] / 1000 for x in lista]
            custos = [x["metricas"]["custo_usd"] or 0 for x in lista]
            w.writerow([
                pid, p["tipo"], p["criterio"], n, corretas, pendentes,
                round(100 * corretas / corrigiveis, 1) if corrigiveis else "",
                round(100 * consistencia, 1),
                len({(x.get("sql") or "").strip() for x in lista if x.get("sql")}),
                "; ".join(f"{k}={v}" for k, v in Counter(x.get("decisao") for x in lista).items()),
                round(statistics.median(tempos), 2), round(max(tempos), 2),
                round(statistics.mean(custos), 6),
            ])

    print(f"Execuções corrigidas: {saida_exec}")
    print(f"Resumo por pergunta:  {saida_resumo}")
    pend = sum(x["situacao"] == "pendente_manual" for v in por_pergunta.values() for x in v)
    if pend:
        print(f"{pend} execuções com critério 'rubrica' aguardam correção manual na coluna 'situacao'.")


if __name__ == "__main__":
    main()
