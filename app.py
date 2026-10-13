"""Servidor web do Indaga.

    uvicorn app:app --reload
"""
import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from indaga import config, esquema, pipeline, registro

app = FastAPI(title="Indaga")
ESTATICOS = Path(__file__).resolve().parent / "static"


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    narrativa: bool = True


def _conferir_senha(senha: str | None) -> None:
    if config.SENHA_ACESSO and not secrets.compare_digest(senha or "", config.SENHA_ACESSO):
        raise HTTPException(status_code=401, detail="Senha de acesso inválida.")


@app.get("/")
def pagina():
    return FileResponse(ESTATICOS / "index.html")


@app.get("/api/config")
def ver_config():
    return {
        "modelo": config.MODELO,
        "esforco": config.ESFORCO,
        "config_hash": pipeline.config_hash(),
        "exige_senha": bool(config.SENHA_ACESSO),
    }


@app.get("/api/esquema")
def ver_esquema(x_senha: str | None = Header(default=None)):
    """O texto exato que o modelo recebe (útil para o apêndice do TCC)."""
    _conferir_senha(x_senha)
    return {"texto": esquema.texto_do_esquema()}


@app.post("/api/perguntar")
async def perguntar(req: Pergunta, x_senha: str | None = Header(default=None)):
    _conferir_senha(x_senha)
    # Teto de consultas da interface pública, para limitar o custo da API.
    usadas = await run_in_threadpool(registro.consultas_24h, "interface")
    if usadas >= config.LIMITE_DIARIO:
        raise HTTPException(status_code=429, detail="Limite diário de consultas atingido. Tente novamente amanhã.")
    resultado = await run_in_threadpool(
        pipeline.responder, req.pergunta.strip(), origem="interface", gerar_narrativa=req.narrativa,
    )
    resultado.pop("sqls_tentados", None)
    return resultado
