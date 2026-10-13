"""Conta as linhas de cada tabela do Olist, antes e depois da coleta.

Uso:
    python scripts/contar_linhas.py antes
    python scripts/contar_linhas.py depois

Grava avaliacao/resultados/contagem_<rotulo>.csv. Com "depois", compara com a
contagem "antes": as duas precisam ser iguais, o que mostra que a coleta não
alterou a base (o Indaga só tem permissão de leitura).
"""
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from indaga import banco, config  # noqa: E402


def contar() -> dict[str, int]:
    with banco.conexao_leitura() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY 1",
            (config.ESQUEMA_DADOS,),
        )
        tabelas = [t for (t,) in cur.fetchall()]
        contagem = {}
        for t in tabelas:
            cur.execute(f'SELECT count(*) FROM {config.ESQUEMA_DADOS}."{t}"')
            contagem[t] = cur.fetchone()[0]
    return contagem


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("antes", "depois"):
        sys.exit(__doc__)
    rotulo = sys.argv[1]
    pasta = RAIZ / "avaliacao" / "resultados"
    contagem = contar()
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with (pasta / f"contagem_{rotulo}.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tabela", "linhas", "contado_em"])
        for t, n in contagem.items():
            w.writerow([t, n, agora])
    for t, n in contagem.items():
        print(f"  {t:<36}{n:>10,}".replace(",", "."))

    anterior = pasta / "contagem_antes.csv"
    if rotulo == "depois" and anterior.exists():
        with anterior.open(encoding="utf-8", newline="") as f:
            antes = {l["tabela"]: int(l["linhas"]) for l in csv.DictReader(f)}
        diferencas = {t: (antes.get(t), contagem.get(t)) for t in set(antes) | set(contagem)
                      if antes.get(t) != contagem.get(t)}
        print("\nIgual à contagem de antes." if not diferencas else f"\nDIFERENÇAS: {diferencas}")


if __name__ == "__main__":
    main()
