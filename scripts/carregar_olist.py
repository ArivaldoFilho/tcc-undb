"""Carrega os CSVs do Brazilian E-Commerce Public Dataset by Olist no PostgreSQL.

Uso:
    python scripts/carregar_olist.py caminho/da/pasta/com/os/csvs [--recriar]

Baixe o dataset no Kaggle e descompacte numa pasta. O script confere o
cabeçalho de cada CSV antes de carregar e para se algo não bater, para que
nenhuma coluna entre trocada. Ao final, imprime a contagem de linhas de cada
tabela (registre esses números no capítulo de metodologia).
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indaga import banco, config  # noqa: E402

TIMESTAMP = "timestamp"
TEXTO = "text"
INTEIRO = "integer"
DINHEIRO = "numeric(12,2)"
# Medidas de produto vêm às vezes com casa decimal no CSV ("40.0").
MEDIDA = "numeric"

# tabela: (arquivo, [(coluna, tipo)], chave primária)
TABELAS = {
    "customers": ("olist_customers_dataset.csv", [
        ("customer_id", TEXTO), ("customer_unique_id", TEXTO),
        ("customer_zip_code_prefix", TEXTO), ("customer_city", TEXTO), ("customer_state", TEXTO),
    ], ["customer_id"]),
    "sellers": ("olist_sellers_dataset.csv", [
        ("seller_id", TEXTO), ("seller_zip_code_prefix", TEXTO),
        ("seller_city", TEXTO), ("seller_state", TEXTO),
    ], ["seller_id"]),
    "product_category_name_translation": ("product_category_name_translation.csv", [
        ("product_category_name", TEXTO), ("product_category_name_english", TEXTO),
    ], ["product_category_name"]),
    "products": ("olist_products_dataset.csv", [
        ("product_id", TEXTO), ("product_category_name", TEXTO),
        ("product_name_lenght", MEDIDA), ("product_description_lenght", MEDIDA),
        ("product_photos_qty", MEDIDA), ("product_weight_g", MEDIDA),
        ("product_length_cm", MEDIDA), ("product_height_cm", MEDIDA), ("product_width_cm", MEDIDA),
    ], ["product_id"]),
    "orders": ("olist_orders_dataset.csv", [
        ("order_id", TEXTO), ("customer_id", TEXTO), ("order_status", TEXTO),
        ("order_purchase_timestamp", TIMESTAMP), ("order_approved_at", TIMESTAMP),
        ("order_delivered_carrier_date", TIMESTAMP), ("order_delivered_customer_date", TIMESTAMP),
        ("order_estimated_delivery_date", TIMESTAMP),
    ], ["order_id"]),
    "order_items": ("olist_order_items_dataset.csv", [
        ("order_id", TEXTO), ("order_item_id", INTEIRO), ("product_id", TEXTO),
        ("seller_id", TEXTO), ("shipping_limit_date", TIMESTAMP),
        ("price", DINHEIRO), ("freight_value", DINHEIRO),
    ], ["order_id", "order_item_id"]),
    "order_payments": ("olist_order_payments_dataset.csv", [
        ("order_id", TEXTO), ("payment_sequential", INTEIRO), ("payment_type", TEXTO),
        ("payment_installments", INTEIRO), ("payment_value", DINHEIRO),
    ], ["order_id", "payment_sequential"]),
    # review_id sozinho se repete na base original (a mesma avaliação vale
    # para mais de um pedido); o par (review_id, order_id) é único.
    "order_reviews": ("olist_order_reviews_dataset.csv", [
        ("review_id", TEXTO), ("order_id", TEXTO), ("review_score", INTEIRO),
        ("review_comment_title", TEXTO), ("review_comment_message", TEXTO),
        ("review_creation_date", TIMESTAMP), ("review_answer_timestamp", TIMESTAMP),
    ], ["review_id", "order_id"]),
    "geolocation": ("olist_geolocation_dataset.csv", [
        ("geolocation_zip_code_prefix", TEXTO), ("geolocation_lat", "double precision"),
        ("geolocation_lng", "double precision"), ("geolocation_city", TEXTO), ("geolocation_state", TEXTO),
    ], None),
}

# Chaves estrangeiras tentadas depois da carga. Se a base violar alguma,
# o script avisa e segue: o relacionamento continua documentado em
# config/descricoes.json, que é o que o modelo lê.
CHAVES_ESTRANGEIRAS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
]


def conferir_cabecalho(caminho: Path, esperadas: list[str]) -> None:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        cabecalho = next(csv.reader(f))
    if cabecalho != esperadas:
        sys.exit(
            f"\nCabeçalho inesperado em {caminho.name}.\n"
            f"  esperado: {esperadas}\n  no arquivo: {cabecalho}\n"
            "Ajuste TABELAS em scripts/carregar_olist.py e rode de novo."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pasta", type=Path, help="pasta com os CSVs do Olist")
    parser.add_argument("--recriar", action="store_true", help="apaga e recria as tabelas existentes")
    args = parser.parse_args()

    s = config.ESQUEMA_DADOS
    arquivos = {}
    for tabela, (arquivo, colunas, _) in TABELAS.items():
        caminho = args.pasta / arquivo
        if not caminho.exists():
            sys.exit(f"Arquivo não encontrado: {caminho}")
        conferir_cabecalho(caminho, [c for c, _ in colunas])
        arquivos[tabela] = caminho
    print("Cabeçalhos conferidos.")

    with banco.conexao_admin() as conn:
        cur = conn.cursor()
        # O PostgreSQL exige CREATE no banco mesmo com IF NOT EXISTS; o usuário
        # da aplicação só é dono do schema, então só cria se ainda não existir.
        cur.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (s,))
        if not cur.fetchone():
            cur.execute(f"CREATE SCHEMA {s}")
        # Ordem inversa para respeitar as chaves estrangeiras ao apagar.
        for tabela in reversed(list(TABELAS)):
            if args.recriar:
                cur.execute(f"DROP TABLE IF EXISTS {s}.{tabela} CASCADE")
        for tabela, (_, colunas, pk) in TABELAS.items():
            defs = [f"{c} {t}" for c, t in colunas]
            if pk:
                defs.append(f"PRIMARY KEY ({', '.join(pk)})")
            cur.execute(f"CREATE TABLE IF NOT EXISTS {s}.{tabela} ({', '.join(defs)})")
            cur.execute(f"SELECT count(*) FROM {s}.{tabela}")
            if cur.fetchone()[0] > 0:
                sys.exit(f"{s}.{tabela} já tem dados. Use --recriar para carregar do zero.")
        conn.commit()

        for tabela, (_, colunas, _) in TABELAS.items():
            nomes = ", ".join(c for c, _ in colunas)
            print(f"Carregando {tabela}...", flush=True)
            with arquivos[tabela].open(encoding="utf-8-sig", newline="") as f:
                cur.copy_expert(f"COPY {s}.{tabela} ({nomes}) FROM STDIN WITH (FORMAT csv, HEADER true)", f)
            conn.commit()

        for origem, col, destino, col_destino in CHAVES_ESTRANGEIRAS:
            nome = f"fk_{origem}_{col}"
            try:
                cur.execute(
                    f"ALTER TABLE {s}.{origem} ADD CONSTRAINT {nome} "
                    f"FOREIGN KEY ({col}) REFERENCES {s}.{destino} ({col_destino})"
                )
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"  aviso: chave estrangeira {nome} não criada ({str(exc).splitlines()[0]})")

        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'indaga_leitor'")
        if cur.fetchone():
            cur.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {s} TO indaga_leitor")
        else:
            print("  aviso: role indaga_leitor não existe. Rode banco/01_estrutura.sql.")
        cur.execute("ANALYZE")
        conn.commit()

        print("\nLinhas por tabela:")
        for tabela in TABELAS:
            cur.execute(f"SELECT count(*) FROM {s}.{tabela}")
            print(f"  {tabela:<36}{cur.fetchone()[0]:>10,}".replace(",", "."))


if __name__ == "__main__":
    main()
