import sqlite3
import os
import uuid
import time
import yaml
from fastapi import FastAPI, Depends, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import Wakeonlan
import ca_manager

app = FastAPI()

# Criar pastas se nao existirem
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Banco de dados SQLite
DB_FILE = "certificados.db"
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS certificados (token TEXT PRIMARY KEY, nome TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def load_config():
    if os.path.exists("config_geral.yml"):
        with open("config_geral.yml", "r") as f:
            return yaml.safe_load(f)
    return {}

config = load_config()
ca_name = config.get("ca_name", "Silas")

@app.on_event("startup")
async def startup_event():
    ca_manager.init_ca(ca_name)

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "senha_super_segura")

# Estado Global
estado_servidor = {
    "status": "Desligado",
    "jogadores": 0,
    "tempo_restante_minutos": 0,
    "ultimo_ping": 0,
    "comando_pendente": None
}

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def verificar_certificado(request: Request):
    # Lê o header com o nome do dono do certificado validado pelo Caddy
    cert_subject = request.headers.get("X-Client-Cert-Subject")
    
    # Se o Caddy encontrou um cert válido, o header terá o nome (ex: CN=Teste)
    # Se falhou ou não tem, ele manda vazio ou a string literal "{tls_client_subject}"
    if cert_subject and cert_subject.strip() != "" and not cert_subject.startswith("{"):
        return True
        
    return False

def verificar_admin(request: Request):
    token = request.cookies.get("minewake_admin")
    if token == "autenticado":
        return True
    return False

# --- Rotas Frontend ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, response: Response, certificado = Depends(verificar_certificado)):
    if not certificado:
        return RedirectResponse(url="/erro", status_code=302)
        
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/erro", response_class=HTMLResponse)
async def erro_page(request: Request):
    return templates.TemplateResponse(request=request, name="erro.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

# --- Rotas API Webhook (Xeon -> Orange Pi) ---
class WebhookData(BaseModel):
    status: str
    jogadores: int
    tempo_restante_minutos: int | None = None

@app.post("/api/webhook")
async def webhook(data: WebhookData):
    global estado_servidor
    estado_servidor["status"] = data.status
    estado_servidor["jogadores"] = data.jogadores
    estado_servidor["tempo_restante_minutos"] = data.tempo_restante_minutos
    estado_servidor["ultimo_ping"] = time.time()
    
    comando = estado_servidor["comando_pendente"]
    estado_servidor["comando_pendente"] = None
    
    return {"status": "ok", "comando": comando}

# --- Rotas API Frontend (Protegidas) ---
@app.get("/api/status")
async def get_status(certificado = Depends(verificar_certificado)):
    if not certificado:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Se passou > 2 min do ultimo ping e não está ligando, assume Desligado
    if estado_servidor["status"] != "Ligando" and time.time() - estado_servidor["ultimo_ping"] > 120:
        estado_servidor["status"] = "Desligado"
        estado_servidor["jogadores"] = 0
        
    return estado_servidor

@app.post("/api/ligar")
async def ligar_servidor(certificado = Depends(verificar_certificado)):
    if not certificado:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    Wakeonlan.enviar_wol()
    estado_servidor["status"] = "Ligando"
    estado_servidor["ultimo_ping"] = time.time()
    return {"message": "WOL enviado!"}

@app.post("/api/renovar")
async def renovar_tempo(certificado = Depends(verificar_certificado)):
    if not certificado:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    estado_servidor["comando_pendente"] = "renovar"
    return {"message": "Comando de renovacao enviado!"}

# --- Rotas API Admin ---
@app.post("/api/admin/login")
async def admin_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = JSONResponse(content={"message": "Login com sucesso"})
        response.set_cookie(key="minewake_admin", value="autenticado")
        return response
    raise HTTPException(status_code=401, detail="Credenciais invalidas")

@app.get("/api/admin/certificados")
async def list_certificados(is_admin = Depends(verificar_admin), db: sqlite3.Connection = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    rows = db.execute("SELECT token, nome, criado_em FROM certificados").fetchall()
    return [{"token": row["token"], "nome": row["nome"], "criado_em": row["criado_em"]} for row in rows]

class CertificadoCreate(BaseModel):
    nome: str

@app.post("/api/admin/certificados")
async def create_certificado(cert: CertificadoCreate, is_admin = Depends(verificar_admin), db: sqlite3.Connection = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    token = str(uuid.uuid4())
    db.execute("INSERT INTO certificados (token, nome) VALUES (?, ?)", (token, cert.nome))
    db.commit()
    
    # Gera o certificado digital com senha padrão "minewake"
    p12_data = ca_manager.generate_client_cert(cert.nome, "minewake")
    
    return Response(
        content=p12_data,
        media_type="application/x-pkcs12",
        headers={"Content-Disposition": f'attachment; filename="{cert.nome}.p12"'}
    )

@app.delete("/api/admin/certificados/{token}")
async def revoke_certificado(token: str, is_admin = Depends(verificar_admin), db: sqlite3.Connection = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    db.execute("DELETE FROM certificados WHERE token = ?", (token,))
    db.commit()
    return {"message": "Certificado revogado"}
