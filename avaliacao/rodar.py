"""Roda o banco de perguntas no Indaga, N vezes cada, sem interface.

Uso:
    python avaliacao/rodar.py --rodada piloto --repeticoes 5
    python avaliacao/rodar.py --rodada teste --repeticoes 1 --ids A1,D1

As repetições são intercaladas (todas as perguntas na repetição 1, depois todas
na 2...), para que uma instabilidade momentânea da API não caia toda sobre a
mesma pergunta. Cada execução é uma sessão nova, sem histórico. Vai para
indaga.execucoes e também para avaliacao/resultados/<rodada>.jsonl, com a data
e o identificador do modelo devolvido pela API.

Falha da API (rede, sobrecarga, limite): uma nova tentativa. Se falhar de
novo, a execução fica marcada com erro_api e o corrigir.py a conta como "erro
de execução", não como resposta errada.

A rodada para se a configuração mudar no meio (config_hash diferente) ou se o
log não puder ser gravado.
"""
import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parent))

from indaga import config, pipeline, registro  # noqa: E402


def ler_perguntas(arquivo: Path, ids: set[str] | None) -> list[dict]:
    with arquivo.open(encoding="utf-8", newline="") as f:
        perguntas = list(csv.DictReader(f))
    if ids:
        faltando = ids - {p["id"] for p in perguntas}
        if faltando:
            sys.exit(f"Ids não encontrados em {arquivo.name}: {sorted(faltando)}")
        perguntas = [p for p in perguntas if p["id"] in ids]
    return perguntas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rodada", required=True, help="nome da rodada, ex.: final_opus55")
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--ids", help="lista de ids separados por vírgula (padrão: todas)")
    parser.add_argument("--arquivo", type=Path, default=PASTA / "perguntas.csv")
    parser.add_argument("--sem-narrativa", action="store_true", help="não gera a explicação em texto")
    parser.add_argument("--pausa", type=float, default=0.0, help="segundos entre execuções")
    args = parser.parse_args()

    ids = {i.strip() for i in args.ids.split(",")} if args.ids else None
    perguntas = ler_perguntas(args.arquivo, ids)
    hash_inicial = pipeline.config_hash()
    total = len(perguntas) * args.repeticoes
    saida = PASTA / "resultados" / f"{args.rodada}.jsonl"
    saida.parent.mkdir(exist_ok=True)
    if saida.exists():
        sys.exit(f"{saida.name} já existe. Use outro nome de rodada para não misturar resultados.")

    print(f"Rodada {args.rodada}: {len(perguntas)} perguntas x {args.repeticoes} = {total} execuções")
    print(f"Modelo {config.MODELO}, esforço {config.ESFORCO}, config_hash {hash_inicial}\n")

    custo_total = 0.0
    feitas = 0
    with saida.open("w", encoding="utf-8") as arq:
        for rep in range(1, args.repeticoes + 1):
            for p in perguntas:
                feitas += 1
                def executar():
                    return pipeline.responder(
                        p["pergunta"], origem="avaliacao", gerar_narrativa=not args.sem_narrativa,
                        rodada=args.rodada, pergunta_id=p["id"], repeticao=rep,
                    )
                r = executar()
                r["tentativas_api"] = 1
                if r["erro_api"]:
                    print(f"      falha da API ({(r['erro'] or '')[:60]}); nova tentativa")
                    erro_anterior = r["erro"]
                    r = executar()
                    r["tentativas_api"], r["erro_api_anterior"] = 2, erro_anterior
                r["pergunta_id"], r["repeticao"], r["rodada"] = p["id"], rep, args.rodada
                r["executado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                r["modelos_api"] = sorted({e["modelo"] for e in r["metricas"]["etapas"] if e.get("modelo")})
                arq.write(registro.para_json(r) + "\n")
                arq.flush()

                m = r["metricas"]
                custo_total += m["custo_usd"] or 0
                situacao = "ok" if r["sucesso"] else f"ERRO: {(r['erro'] or '')[:80]}"
                print(f"[{feitas:>3}/{total}] {p['id']:<5} rep {rep}  {r['decisao'] or '-':<14} "
                      f"{m['tempo_total_ms'] / 1000:>6.1f}s  US$ {m['custo_usd'] or 0:.4f}  {situacao}")

                if r["erro_registro"]:
                    sys.exit(f"\nFalha ao gravar no banco: {r['erro_registro']}\nRodada interrompida.")
                if m["config_hash"] != hash_inicial:
                    sys.exit("\nA configuração mudou durante a rodada. Rodada interrompida.")
                if args.pausa:
                    time.sleep(args.pausa)

    print(f"\nConcluído. Custo total estimado: US$ {custo_total:.4f}")
    print(f"Resultados em {saida}")
    print(f"Próximo passo: python avaliacao/corrigir.py --rodada {args.rodada}")


if __name__ == "__main__":
    main()
