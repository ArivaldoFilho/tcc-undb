"""Cria as tabelas do estudo com usuários (banco/02_estudo.sql).

Uso:
    python scripts/criar_estudo.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from indaga import banco  # noqa: E402


def main() -> None:
    sql = (RAIZ / "banco" / "02_estudo.sql").read_text(encoding="utf-8")
    with banco.conexao_admin() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'indaga' AND table_name LIKE 'estudo%%' ORDER BY 1"
            )
            tabelas = [t for (t,) in cur.fetchall()]
        conn.commit()
    print("Tabelas do estudo:", ", ".join(tabelas))


if __name__ == "__main__":
    main()
