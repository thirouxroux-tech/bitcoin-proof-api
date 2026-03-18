from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import hashlib
import uuid
import json
import os
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

PROOFS_FILE = "proofs.json"

# ======================
# FILE STORAGE
# ======================

def load_proofs():
    if not os.path.exists(PROOFS_FILE):
        return []
    with open(PROOFS_FILE, "r") as f:
        return json.load(f)

def save_proofs(data):
    with open(PROOFS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ======================
# HTML ROUTES
# ======================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/verify-page", response_class=HTMLResponse)
def verify_page(request: Request):
    return templates.TemplateResponse("verify.html", {"request": request})


@app.get("/explorer", response_class=HTMLResponse)
def explorer_page(request: Request):
    return templates.TemplateResponse("explorer.html", {"request": request})


@app.get("/proof-page/{vid}", response_class=HTMLResponse)
def proof_page(request: Request, vid: str):

    proofs = load_proofs()

    for p in proofs:
        if p["verification_id"] == vid:
            return templates.TemplateResponse(
                "proof.html",
                {"request": request, "proof": p}
            )

    return HTMLResponse("Proof not found", status_code=404)

# ======================
# API
# ======================

@app.post("/verify")
def verify(data: dict):

    message = data.get("message", "")

    if message == "":
        return {"error": "empty message"}

    message_hash = hashlib.sha256(message.encode()).hexdigest()
    vid = str(uuid.uuid4())[:8]

    proof = {
        "verification_id": vid,
        "message_hash": message_hash,
        "timestamp": datetime.utcnow().isoformat()
    }

    proofs = load_proofs()
    proofs.append(proof)
    save_proofs(proofs)

    return proof


@app.get("/proofs")
def get_proofs():
    return load_proofs()
app.mount("/static", StaticFiles(directory="static"), name="static")