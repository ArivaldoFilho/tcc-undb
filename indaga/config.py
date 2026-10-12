"""Configuração do Indaga, lida do arquivo .env na raiz do projeto.

Tudo o que influencia a resposta do modelo (modelo, esforço, temperatura,
prompts e descrições do esquema) entra no hash de configuração gravado em cada
execução. Assim é possível provar que a configuração ficou congelada durante o
experimento.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def _env(nome: str, padrao: str = "") -> str:
    return (os.getenv(nome) or padrao).strip()


# ── Modelo ────────────────────────────────────────────────────────────────
MODELO = _env("INDAGA_MODELO", "claude-opus-5-5")
# low | medium | high | xhigh | max. No Opus 5.5 o padrão da API é medium;
# fixamos explicitamente para que a configuração fique documentada.
ESFORCO = _env("INDAGA_ESFORCO", "medium")
# Vazio = não envia. O Opus 5.5 rejeita temperature (erro 400); só preencha
# se trocar para um modelo que aceite o parâmetro (ex.: claude-sonnet-4-6).
TEMPERATURA = _env("INDAGA_TEMPERATURA")

# Preço em USD por milhão de tokens (entrada, saída). Tabela consultada em
# out. 2026; confira na página oficial de preços na data do experimento e
# sobrescreva com INDAGA_PRECO_ENTRADA / INDAGA_PRECO_SAIDA se mudou.
PRECOS_USD_POR_MTOK = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-4-6": (3.00, 15.00),
}
PRECO_ENTRADA = _env("INDAGA_PRECO_ENTRADA")
PRECO_SAIDA = _env("INDAGA_PRECO_SAIDA")

# ── Banco ─────────────────────────────────────────────────────────────────
# Conexão administrativa: carga do Olist, leitura do esquema e gravação do log.
DATABASE_URL = _env("DATABASE_URL")
# Conexão do usuário somente leitura que executa o SQL gerado pela IA.
DATABASE_URL_LEITURA = _env("DATABASE_URL_LEITURA")
ESQUEMA_DADOS = _env("INDAGA_ESQUEMA_DADOS", "olist")

MAX_LINHAS = 500
MAX_TENTATIVAS_SQL = 3          # 1 geração + até 2 correções
TIMEOUT_SQL_SEGUNDOS = 20
MAX_LINHAS_NARRATIVA = 50       # linhas do resultado enviadas ao modelo na narrativa

# ── Acesso ────────────────────────────────────────────────────────────────
# Se preenchida, a interface pede essa senha (útil no estudo com usuários).
SENHA_ACESSO = _env("INDAGA_SENHA_ACESSO")

ARQUIVO_DESCRICOES = RAIZ / "config" / "descricoes.json"
