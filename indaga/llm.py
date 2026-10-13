"""Chamada à Messages API do Claude, com medição de tokens e latência."""
import time
from dataclasses import dataclass

import anthropic

from . import config

_cliente: anthropic.Anthropic | None = None


def cliente() -> anthropic.Anthropic:
    global _cliente
    if _cliente is None:
        # Sem retry automático do SDK: uma nova tentativa silenciosa somaria
        # latência sem aparecer no log. Falhas de rede viram erro registrado.
        _cliente = anthropic.Anthropic(max_retries=0, timeout=180.0)
    return _cliente


class RecusaDoModelo(RuntimeError):
    """O modelo encerrou com stop_reason == "refusal"."""


@dataclass
class Chamada:
    etapa: str
    texto: str
    tokens_entrada: int
    tokens_saida: int
    ms: int
    stop_reason: str
    request_id: str | None
    modelo: str | None = None

    def como_dict(self) -> dict:
        return {
            "etapa": self.etapa,
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "ms": self.ms,
            "stop_reason": self.stop_reason,
            "request_id": self.request_id,
            "modelo": self.modelo,
        }


def chamar(
    etapa: str,
    *,
    system: str,
    mensagens: list[dict],
    max_tokens: int,
    formato_json: dict | None = None,
) -> Chamada:
    params: dict = {
        "model": config.MODELO,
        "max_tokens": max_tokens,
        "system": system,
        "messages": mensagens,
    }
    output_config: dict = {}
    if config.ESFORCO:
        output_config["effort"] = config.ESFORCO
    if formato_json:
        output_config["format"] = {"type": "json_schema", "schema": formato_json}
    if output_config:
        params["output_config"] = output_config
    if config.TEMPERATURA:
        params["temperature"] = float(config.TEMPERATURA)

    inicio = time.perf_counter()
    resposta = cliente().messages.create(**params)
    ms = int((time.perf_counter() - inicio) * 1000)

    if resposta.stop_reason == "refusal":
        raise RecusaDoModelo(f"O modelo recusou a etapa '{etapa}'.")

    # Com raciocínio adaptativo a resposta traz blocos de thinking antes do
    # texto; só o texto interessa. Os tokens de raciocínio entram em output_tokens.
    texto = "".join(b.text for b in resposta.content if b.type == "text")
    return Chamada(
        etapa=etapa,
        texto=texto,
        tokens_entrada=resposta.usage.input_tokens,
        tokens_saida=resposta.usage.output_tokens,
        ms=ms,
        stop_reason=resposta.stop_reason or "",
        request_id=getattr(resposta, "_request_id", None),
        modelo=getattr(resposta, "model", None),
    )


def custo_usd(tokens_entrada: int, tokens_saida: int) -> float | None:
    if config.PRECO_ENTRADA and config.PRECO_SAIDA:
        entrada, saida = float(config.PRECO_ENTRADA), float(config.PRECO_SAIDA)
    elif config.MODELO in config.PRECOS_USD_POR_MTOK:
        entrada, saida = config.PRECOS_USD_POR_MTOK[config.MODELO]
    else:
        return None
    return round((tokens_entrada * entrada + tokens_saida * saida) / 1_000_000, 6)
