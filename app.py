"""Servidor web do Indaga.

    uvicorn app:app --reload
"""
import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from indaga import config, esquema, estudo, pipeline

app = FastAPI(title="Indaga")
ESTATICOS = Path(__file__).resolve().parent / "static"


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    participante: str | None = Field(default=None, max_length=40)
    narrativa: bool = True
    estudo_pergunta_id: str | None = Field(default=None, max_length=10)


def _conferir_senha(senha: str | None) -> None:
    if config.SENHA_ACESSO and not secrets.compare_digest(senha or "", config.SENHA_ACESSO):
        raise HTTPException(status_code=401, detail="Senha de acesso inválida.")


@app.exception_handler(estudo.ErroEstudo)
async def _erro_estudo(_: Request, exc: estudo.ErroEstudo):
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})


# A raiz é a página do estudo: é o link enviado aos participantes. A interface
# livre do Indaga fica em /indaga, protegida por INDAGA_SENHA_ACESSO.
@app.get("/")
def pagina_estudo():
    return FileResponse(ESTATICOS / "estudo.html")


@app.get("/estudo")
def estudo_antigo(request: Request):
    destino = "/" + (f"?{request.url.query}" if request.url.query else "")
    return RedirectResponse(destino, status_code=308)


@app.get("/indaga")
def pagina_indaga():
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
async def perguntar(
    req: Pergunta,
    x_senha: str | None = Header(default=None),
    x_estudo_token: str | None = Header(default=None),
):
    if x_estudo_token:
        # Dentro do estudo, o token do participante substitui a senha de acesso.
        participante, rodada = await run_in_threadpool(
            estudo.autorizar_consulta_ia, x_estudo_token, req.estudo_pergunta_id
        )
        origem, pergunta_id = "estudo", req.estudo_pergunta_id
    else:
        _conferir_senha(x_senha)
        participante = (req.participante or "").strip() or None
        origem, pergunta_id, rodada = "interface", None, None
    resultado = await run_in_threadpool(
        pipeline.responder,
        req.pergunta.strip(),
        origem=origem,
        gerar_narrativa=req.narrativa,
        participante=participante,
        pergunta_id=pergunta_id,
        rodada=rodada,
    )
    resultado.pop("sqls_tentados", None)
    return resultado


# ── Estudo com usuários ──────────────────────────────────────────────────
class InicioEstudo(BaseModel):
    consentimento: bool
    perfil: dict
    piloto: bool = False


class RespostaEstudo(BaseModel):
    pergunta_id: str = Field(max_length=10)
    situacao: str
    resposta: str | None = Field(default=None, max_length=2000)
    confianca: int | None = None
    conferiu: bool | None = None
    tempo_ms: int | None = None
    tempo_total_ms: int | None = None


class SusEstudo(BaseModel):
    ferramenta: str
    itens: list[int]


class FimEstudo(BaseModel):
    preferencias: dict
    comentarios: str | None = Field(default=None, max_length=4000)


class EventoEstudo(BaseModel):
    pergunta_id: str | None = Field(default=None, max_length=10)
    tipo: str
    execucao_id: int | None = None


@app.post("/api/estudo/iniciar")
async def estudo_iniciar(req: InicioEstudo, user_agent: str | None = Header(default=None)):
    if not req.consentimento:
        raise HTTPException(status_code=400, detail="É preciso concordar com o termo para participar.")
    return await run_in_threadpool(estudo.iniciar, req.perfil, req.piloto, user_agent)


@app.get("/api/estudo/estado")
async def estudo_estado(x_estudo_token: str = Header()):
    return await run_in_threadpool(estudo.estado, x_estudo_token)


@app.post("/api/estudo/resposta")
async def estudo_resposta(req: RespostaEstudo, x_estudo_token: str = Header()):
    await run_in_threadpool(estudo.responder, x_estudo_token, req.model_dump())
    return {"ok": True}


@app.post("/api/estudo/sus")
async def estudo_sus(req: SusEstudo, x_estudo_token: str = Header()):
    await run_in_threadpool(estudo.registrar_sus, x_estudo_token, req.ferramenta, req.itens)
    return {"ok": True}


@app.post("/api/estudo/concluir")
async def estudo_concluir(req: FimEstudo, x_estudo_token: str = Header()):
    await run_in_threadpool(estudo.concluir, x_estudo_token, req.preferencias, req.comentarios)
    return {"ok": True}


@app.post("/api/estudo/evento")
async def estudo_evento(req: EventoEstudo, x_estudo_token: str = Header()):
    await run_in_threadpool(estudo.registrar_evento, x_estudo_token, req.pergunta_id, req.tipo, req.execucao_id)
    return {"ok": True}


@app.get("/api/estudo/info")
def estudo_info():
    """Dados públicos do estudo, para o termo de consentimento."""
    return {"termo": estudo.configuracao()["termo"]}
