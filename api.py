from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import hashlib
import json
import uuid
import datetime
import os

app = FastAPI()

# ---------- WEBSITE ----------

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
@app.get("/explorer", response_class=HTMLResponse)
def explorer(request: Request):
    return templates.TemplateResponse(
        "explorer.html",
        {"request": request}
    )
@app.get("/explorer", response_class=HTMLResponse)
def explorer_page(request: Request):
    return templates.TemplateResponse(
        "explorer.html",
        {"request": request}
    )


# ---------- DATABASE ----------

DB_FILE = "proofs.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)


def load_proofs():
    with open(DB_FILE) as f:
        return json.load(f)


def save_proofs(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------- API KEY ----------

API_KEY = os.getenv("API_KEY", "dev_key_123456")


def check_key(key):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ---------- ROOT API ----------

@app.get("/api")
def api_status():
    return {"status": "Bitcoin Proof API running"}


# ---------- VERIFY SIGNATURE ----------

@app.post("/verify")
def verify(
    data: dict,
    x_api_key: str = Header(None)
):

    check_key(x_api_key)

    address = data.get("address")
    message = data.get("message")
    signature = data.get("signature")

    if not address or not message or not signature:
        raise HTTPException(status_code=400, detail="Missing fields")

    message_hash = hashlib.sha256(message.encode()).hexdigest()

    proof = {
        "verification_id": str(uuid.uuid4())[:8],
        "address": address,
        "message": message,
        "signature": signature,
        "message_hash": message_hash,
        "timestamp": str(datetime.datetime.utcnow()),
        "status": "valid"
    }

    proofs = load_proofs()
    proofs.append(proof)
    save_proofs(proofs)

    return proof


# ---------- LIST PROOFS ----------

@app.get("/proofs")
def get_proofs():
    return load_proofs()


# ---------- SINGLE PROOF ----------

@app.get("/proof/{proof_id}")
def get_proof(proof_id: str):

    proofs = load_proofs()

    for p in proofs:
        if p["verification_id"] == proof_id:
            return p

    raise HTTPException(status_code=404, detail="Proof not found")

    <p>
    <a href="/dashboard">Dashboard</a>
    </p>

    </body>
    </html>
    """

@app.get("/dashboard")
def dashboard():

    file="dashboard.html"

    if os.path.exists(file):
        return FileResponse(file)

    return {"error":"dashboard.html not found"}



