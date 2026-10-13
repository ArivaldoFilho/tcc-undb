"""Corrige uma rodada contra o gabarito e calcula as métricas por pergunta.

Uso:
    python avaliacao/corrigir.py --rodada final
    python avaliacao/corrigir.py --rodada participantes --arquivo avaliacao/perguntas_participantes.csv

Gera, em avaliacao/resultados/:
    <rodada>_execucoes.csv   uma linha por execução, com a correção automática e a final
    <rodada>_revisao.csv     o que precisa de olhar humano (ver abaixo); é preenchido à mão
    <rodada>_resumo.csv      uma linha por pergunta: acerto, consistência, tempo, custo

A unidade avaliada é a resposta final que o usuário lê (resultado e explicação),
não só o SQL.

Critérios automáticos (coluna "criterio", definidos ANTES da coleta):
    numero      uma linha no resultado e alguma célula igual ao gabarito, dentro
                da tolerância (absoluta, ou relativa se terminar em %)
    percentual  como numero, com o gabarito em pontos percentuais (8.11 = 8,11%);
                aceita a resposta em pontos (8.11) ou em fração (0.0811)
    lista       alguma coluna do resultado tem o mesmo conjunto de valores da
                primeira coluna do gabarito (a ordem não conta)
    tabela      mesmo multiconjunto de linhas (a ordem não conta)
    recusa      correto se a decisão foi sem_dados ou esclarecimento; se a IA
                executou SQL e explicou, vai para revisão (a explicação pode
                avisar que falta o dado, o que também é correto)
    rubrica     vai para revisão
Falha da API depois da nova tentativa do rodar.py: "erro_execucao", fora da
taxa de acerto.

Revisão manual (<rodada>_revisao.csv). Entram: pendentes (recusa e rubrica),
incorretos e falhas (reconferir o gabarito antes de contar o erro) e
explicações com números que não aparecem no resultado. Colunas a preencher:
    avaliador_1, avaliador_2   correto | incorreto, cada um sem ver o outro
    veredito_final             correto | incorreto | erro_execucao (consenso)
    explicacao_errada          sim, se o resultado está certo e o texto errado
Ao rodar de novo, os vereditos preenchidos substituem a correção automática e o
que já foi escrito é preservado. A concordância sai de avaliacao/concordancia.py.
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
    if execucao.get("erro_api"):
        return "erro_execucao"
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


CAMPOS_REVISAO = ["chave", "id_registro", "pergunta_id", "tipo", "criterio", "repeticao", "situacao_automatica",
                  "motivo_revisao", "pergunta", "criterio_de_correcao", "resposta_ia", "resultado", "sql",
                  "numeros_narrativa_a_revisar", "avaliador_1", "avaliador_2", "veredito_final",
                  "explicacao_errada", "observacao_revisao"]
PREENCHIDOS = ["avaliador_1", "avaliador_2", "veredito_final", "explicacao_errada", "observacao_revisao"]


def _ler_revisao(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8", newline="") as f:
        return {l["chave"]: l for l in csv.DictReader(f)}


def _ordem(pid: str):
    return (pid[:1], int(pid[1:]) if pid[1:].isdigit() else 0, pid)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rodada", required=True)
    parser.add_argument("--arquivo", type=Path, default=PASTA / "perguntas.csv")
    args = parser.parse_args()

    res = PASTA / "resultados"
    entrada = res / f"{args.rodada}.jsonl"
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

    caminho_revisao = res / f"{args.rodada}_revisao.csv"
    revisao_anterior = _ler_revisao(caminho_revisao)
    revisao, por_pergunta = [], defaultdict(list)
    with (res / f"{args.rodada}_execucoes.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id_registro", "pergunta_id", "tipo", "repeticao", "decisao", "situacao_automatica",
                    "situacao", "assinatura_resultado", "n_linhas", "tentativas", "tentativas_api", "tempo_s",
                    "tokens_entrada", "tokens_saida", "custo_usd", "numeros_narrativa_a_revisar", "erro", "sql"])
        for e in execucoes:
            p = perguntas[e["pergunta_id"]]
            chave = f"{e['pergunta_id']}#{e['repeticao']}"
            automatica = corrigir(e, p, gabaritos.get(e["pergunta_id"]))
            suspeitos = numeros_sem_correspondencia(e.get("narrativa"), e.get("linhas") or [])
            anterior = revisao_anterior.get(chave, {})
            situacao = (anterior.get("veredito_final") or "").strip() or automatica
            motivos = []
            if automatica == "pendente_manual":
                motivos.append("julgamento (recusa ou rubrica)")
            if automatica in ("incorreto", "falha"):
                motivos.append("erro: reconferir o gabarito")
            if suspeitos:
                motivos.append("números da explicação fora do resultado")
            if motivos:
                revisao.append({
                    "chave": chave, "id_registro": e.get("id"), "pergunta_id": e["pergunta_id"], "tipo": p["tipo"],
                    "criterio": p["criterio"], "repeticao": e["repeticao"], "situacao_automatica": automatica,
                    "motivo_revisao": "; ".join(motivos), "pergunta": p["pergunta"],
                    "criterio_de_correcao": p.get("observacao", ""),
                    "resposta_ia": e.get("narrativa") or e.get("mensagem") or e.get("erro") or "",
                    "resultado": json.dumps((e.get("linhas") or [])[:10], ensure_ascii=False, default=str),
                    "sql": e.get("sql") or "", "numeros_narrativa_a_revisar": "; ".join(suspeitos),
                    **{c: anterior.get(c, "") for c in PREENCHIDOS},
                })
            assinatura = _assinatura(e.get("linhas") or []) if e.get("decisao") == "sql" and e.get("sucesso") else ""
            m = e["metricas"]
            por_pergunta[e["pergunta_id"]].append({**e, "situacao": situacao, "assinatura": assinatura,
                                                   "explicacao_errada": anterior.get("explicacao_errada", "")})
            w.writerow([e.get("id"), e["pergunta_id"], p["tipo"], e["repeticao"], e.get("decisao"), automatica,
                        situacao, assinatura, e.get("n_linhas"), e.get("tentativas"), e.get("tentativas_api", 1),
                        round(m["tempo_total_ms"] / 1000, 2), m["tokens_entrada"], m["tokens_saida"], m["custo_usd"],
                        "; ".join(suspeitos), e.get("erro") or "", e.get("sql") or ""])

    with caminho_revisao.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_REVISAO)
        w.writeheader()
        w.writerows(revisao)

    with (res / f"{args.rodada}_resumo.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pergunta_id", "tipo", "criterio", "execucoes", "corretas", "incorretas", "pendentes_manual",
                    "erros_execucao", "taxa_acerto_pct", "consistencia_resultado_pct", "sqls_distintos", "decisoes",
                    "explicacao_errada", "tempo_mediano_s", "tempo_max_s", "custo_medio_usd"])
        for pid in sorted(por_pergunta, key=_ordem):
            lista, p = por_pergunta[pid], perguntas[pid]
            validas = [x for x in lista if x["situacao"] != "erro_execucao"]
            corretas = sum(x["situacao"] == "correto" for x in validas)
            pendentes = sum(x["situacao"] == "pendente_manual" for x in validas)
            julgadas = len(validas) - pendentes
            # Consistência: fração das execuções no resultado (ou na decisão) mais frequente.
            chaves = [x["assinatura"] or f"decisao:{x.get('decisao')}" for x in validas]
            consistencia = Counter(chaves).most_common(1)[0][1] / len(validas) if validas else None
            tempos = [x["metricas"]["tempo_total_ms"] / 1000 for x in validas] or [0]
            custos = [x["metricas"]["custo_usd"] or 0 for x in lista]
            w.writerow([
                pid, p["tipo"], p["criterio"], len(lista), corretas, julgadas - corretas, pendentes,
                len(lista) - len(validas), round(100 * corretas / julgadas, 1) if julgadas else "",
                round(100 * consistencia, 1) if consistencia is not None else "",
                len({(x.get("sql") or "").strip() for x in validas if x.get("sql")}),
                "; ".join(f"{k}={v}" for k, v in Counter(x.get("decisao") for x in validas).items()),
                sum((x["explicacao_errada"] or "").strip().lower() == "sim" for x in lista),
                round(statistics.median(tempos), 2), round(max(tempos), 2), round(statistics.mean(custos), 6),
            ])

    pend = sum(x["situacao"] == "pendente_manual" for v in por_pergunta.values() for x in v)
    print(f"Resultados em {res} ({args.rodada}_execucoes, _revisao, _resumo).")
    print(f"{len(revisao)} execuções para revisão; {pend} ainda sem veredito final.")


if __name__ == "__main__":
    main()
