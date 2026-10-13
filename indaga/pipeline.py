"""Fluxo de uma pergunta: decisão e SQL, guardrail, execução com correção,
narrativa e registro.

Diferenças deliberadas em relação a um produto comercial, para que o
experimento seja reprodutível: sem cache de resultado, sem exemplos tirados do
histórico (few-shot) e sem seleção de tabelas por similaridade. Cada execução
recebe exatamente o mesmo contexto, então a variação entre repetições vem só
do modelo.
"""
import hashlib
import json
import time

import anthropic

from . import banco, config, esquema, llm, prompts, registro


def config_hash() -> str:
    """Identifica a configuração exata que gerou cada resposta."""
    partes = {
        "modelo": config.MODELO,
        "esforco": config.ESFORCO,
        "temperatura": config.TEMPERATURA,
        "max_tentativas": config.MAX_TENTATIVAS_SQL,
        "max_linhas_narrativa": config.MAX_LINHAS_NARRATIVA,
        "prompts": [
            prompts.SISTEMA_SQL, prompts.FORMATO_DECISAO, prompts.CORRECAO,
            prompts.SISTEMA_NARRATIVA, prompts.USUARIO_NARRATIVA,
        ],
        "esquema": esquema.texto_do_esquema(),
    }
    bruto = json.dumps(partes, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:16]


def _decidir(mensagens: list[dict], chamadas: list, etapa: str) -> dict:
    sistema = prompts.SISTEMA_SQL.format(esquema=esquema.texto_do_esquema())
    chamada = llm.chamar(
        etapa, system=sistema, mensagens=mensagens,
        max_tokens=16000, formato_json=prompts.FORMATO_DECISAO,
    )
    chamadas.append(chamada)
    decisao = json.loads(chamada.texto)
    decisao["_bruto"] = chamada.texto
    return decisao


def _tabela_texto(colunas: list[str], linhas: list[list]) -> str:
    cab = " | ".join(colunas)
    corpo = [" | ".join("" if v is None else str(v) for v in linha) for linha in linhas]
    return "\n".join([cab, *corpo])


def _narrar(pergunta: str, suposicoes: list[str], colunas, linhas, truncado, chamadas) -> str:
    if not linhas:
        return "A consulta não retornou nenhuma linha."
    mostradas = linhas[: config.MAX_LINHAS_NARRATIVA]
    usuario = prompts.USUARIO_NARRATIVA.format(
        pergunta=pergunta,
        suposicoes="\n".join(f"- {s}" for s in suposicoes) or "- nenhuma",
        n_linhas=len(linhas),
        aviso_truncado=", truncado no limite do sistema" if truncado else "",
        max_linhas=config.MAX_LINHAS_NARRATIVA,
        tabela=_tabela_texto(colunas, mostradas),
    )
    chamada = llm.chamar(
        "narrativa", system=prompts.SISTEMA_NARRATIVA,
        mensagens=[{"role": "user", "content": usuario}], max_tokens=4000,
    )
    chamadas.append(chamada)
    return chamada.texto.strip()


def responder(
    pergunta: str,
    *,
    origem: str = "interface",
    gerar_narrativa: bool = True,
    rodada: str | None = None,
    pergunta_id: str | None = None,
    repeticao: int | None = None,
    participante: str | None = None,
) -> dict:
    inicio = time.perf_counter()
    chamadas: list[llm.Chamada] = []
    etapas_banco: list[dict] = []
    r: dict = {
        "pergunta": pergunta, "decisao": None, "sql": None, "mensagem": None,
        "suposicoes": [], "colunas": [], "linhas": [], "n_linhas": 0, "truncado": False,
        "narrativa": None, "sucesso": False, "erro": None, "tentativas": 0,
        "sqls_tentados": [], "erro_api": False,
    }

    try:
        mensagens = [{"role": "user", "content": pergunta}]
        decisao = _decidir(mensagens, chamadas, "decisao")
        r["decisao"] = decisao["decisao"]
        r["mensagem"] = decisao.get("mensagem") or None
        r["suposicoes"] = decisao.get("suposicoes") or []

        if decisao["decisao"] != "sql":
            r["sucesso"] = True
        else:
            for tentativa in range(1, config.MAX_TENTATIVAS_SQL + 1):
                sql = (decisao.get("sql") or "").strip()
                r["tentativas"] = tentativa
                r["sql"] = sql
                r["sqls_tentados"].append(sql)
                motivo = banco.violacao_guardrail(sql)
                if motivo:
                    # Guardrail não entra no ciclo de correção: é bloqueio, não erro.
                    r["erro"] = f"Bloqueado pelo guardrail: {motivo}"
                    break
                t0 = time.perf_counter()
                try:
                    colunas, linhas, truncado = banco.executar_leitura(sql)
                    etapas_banco.append({"etapa": f"execucao_{tentativa}", "ms": int((time.perf_counter() - t0) * 1000), "ok": True})
                    r.update(colunas=colunas, linhas=linhas, n_linhas=len(linhas), truncado=truncado, sucesso=True, erro=None)
                    break
                except Exception as exc:  # erro do banco: devolve ao modelo para corrigir
                    erro_banco = str(exc).strip()
                    etapas_banco.append({"etapa": f"execucao_{tentativa}", "ms": int((time.perf_counter() - t0) * 1000), "ok": False, "erro": erro_banco})
                    r["erro"] = erro_banco
                    if tentativa == config.MAX_TENTATIVAS_SQL:
                        break
                    mensagens = mensagens + [
                        {"role": "assistant", "content": decisao["_bruto"]},
                        {"role": "user", "content": prompts.CORRECAO.format(erro=erro_banco)},
                    ]
                    decisao = _decidir(mensagens, chamadas, f"correcao_{tentativa}")
                    r["suposicoes"] = decisao.get("suposicoes") or r["suposicoes"]
                    if decisao["decisao"] != "sql":
                        r["decisao"] = decisao["decisao"]
                        r["mensagem"] = decisao.get("mensagem") or None
                        r["sucesso"] = True
                        r["erro"] = None
                        break

            if r["sucesso"] and r["decisao"] == "sql" and gerar_narrativa:
                r["narrativa"] = _narrar(pergunta, r["suposicoes"], r["colunas"], r["linhas"], r["truncado"], chamadas)
    except llm.RecusaDoModelo as exc:
        r["erro"] = str(exc)
    except Exception as exc:
        r["erro"] = f"{type(exc).__name__}: {exc}"
        r["erro_api"] = isinstance(exc, anthropic.APIError)

    tokens_entrada = sum(c.tokens_entrada for c in chamadas)
    tokens_saida = sum(c.tokens_saida for c in chamadas)
    r["metricas"] = {
        "modelo": config.MODELO,
        "esforco": config.ESFORCO,
        "config_hash": config_hash(),
        "tempo_total_ms": int((time.perf_counter() - inicio) * 1000),
        "tokens_entrada": tokens_entrada,
        "tokens_saida": tokens_saida,
        "custo_usd": llm.custo_usd(tokens_entrada, tokens_saida),
        "etapas": [c.como_dict() for c in chamadas] + etapas_banco,
    }
    # Falha no log não pode apagar a resposta já obtida (e já paga): o
    # chamador decide o que fazer. O script de avaliação interrompe a rodada.
    try:
        r["id"] = registro.gravar(
            r, origem=origem, rodada=rodada, pergunta_id=pergunta_id,
            repeticao=repeticao, participante=participante,
        )
        r["erro_registro"] = None
    except Exception as exc:
        r["id"] = None
        r["erro_registro"] = f"{type(exc).__name__}: {exc}"
    return r
