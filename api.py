from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
import json
import os
import hashlib
import uuid
import datetime

app = FastAPI()

# -----------------------
# FILES
# -----------------------

BASE_DIR = os.path.dirname(__file__)

INDEX_FILE = os.path.join(BASE_DIR, "templates", "index.html")
EXPLORER_FILE = os.path.join(BASE_DIR, "templates", "explorer.html")

DB_FILE = os.path.join(BASE_DIR, "proofs.json")


# -----------------------
# DATABASE
# -----------------------

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)


def load_proofs():
    with open(DB_FILE) as f:
        return json.load(f)


def save_proofs(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------
# API KEY
# -----------------------

API_KEY = os.getenv("API_KEY", "dev_key_123456")


def check_key(key):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# -----------------------
# HOME PAGE
# -----------------------

@app.get("/", response_class=HTMLResponse)
def home():

    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE) as f:
            return f.read()

    return "<h1>index.html not found</h1>"


# -----------------------
# EXPLORER PAGE
# -----------------------

@app.get("/explorer", response_class=HTMLResponse)
def explorer():

    if os.path.exists(EXPLORER_FILE):
        with open(EXPLORER_FILE) as f:
            return f.read()

    return "<h1>explorer.html not found</h1>"


# -----------------------
# API STATUS
# -----------------------

@app.get("/api")
def api():
    return {"status": "Bitcoin Proof API running"}


# -----------------------
# VERIFY
# -----------------------

@app.post("/verify")
def verify(data: dict, x_api_key: str = Header(None)):

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


# -----------------------
# LIST PROOFS
# -----------------------

@app.get("/proofs")
def proofs():
    return load_proofs()


# -----------------------
# SINGLE PROOF
# -----------------------

@app.get("/proof/{proof_id}")
def proof(proof_id: str):

    proofs = load_proofs()

    for p in proofs:
        if p["verification_id"] == proof_id:
            return p

    return {"error": "Proof not found"}



