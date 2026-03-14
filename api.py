from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import hashlib
import json
import os
import uuid
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")

API_KEY = os.getenv("API_KEY", "dev_key_123456")

PROOF_FILE = "proofs.json"


# -------------------------
# utils
# -------------------------

def load_proofs():
    if not os.path.exists(PROOF_FILE):
        return []
    with open(PROOF_FILE, "r") as f:
        return json.load(f)


def save_proofs(proofs):
    with open(PROOF_FILE, "w") as f:
        json.dump(proofs, f, indent=4)


def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


# -------------------------
# merkle tree
# -------------------------

def merkle_root(hashes):

    if len(hashes) == 0:
        return None

    layer = hashes

    while len(layer) > 1:

        new_layer = []

        for i in range(0, len(layer), 2):

            left = layer[i]

            if i + 1 < len(layer):
                right = layer[i + 1]
            else:
                right = left

            new_hash = sha256(left + right)

            new_layer.append(new_hash)

        layer = new_layer

    return layer[0]


# -------------------------
# routes
# -------------------------

@app.get("/")
def root():
    return {"status": "Bitcoin Proof API running"}


# -------------------------
# verify
# -------------------------

@app.post("/verify")
async def verify(request: Request):

    key = request.headers.get("X-API-KEY")

    if key != API_KEY:
        return {"error": "unauthorized"}

    data = await request.json()

    address = data.get("address")
    message = data.get("message")
    signature = data.get("signature")

    if not message:
        return {"error": "message missing"}

    message_hash = sha256(message)

    proof = {
        "verification_id": str(uuid.uuid4())[:8],
        "address": address,
        "message": message,
        "signature": signature,
        "message_hash": message_hash,
        "timestamp": datetime.utcnow().isoformat()
    }

    proofs = load_proofs()
    proofs.append(proof)
    save_proofs(proofs)

    return proof


# -------------------------
# proofs list
# -------------------------

@app.get("/proofs")
def get_proofs():

    proofs = load_proofs()

    return {
        "count": len(proofs),
        "proofs": proofs
    }


# -------------------------
# merkle root
# -------------------------

@app.get("/merkle")
def get_merkle():

    proofs = load_proofs()

    hashes = [p["message_hash"] for p in proofs]

    root = merkle_root(hashes)

    return {
        "proof_count": len(hashes),
        "merkle_root": root
    }


# -------------------------
# bitcoin anchor preparation
# -------------------------

@app.get("/anchor")
def anchor():

    proofs = load_proofs()

    hashes = [p["message_hash"] for p in proofs]

    root = merkle_root(hashes)

    if root is None:
        return {"error": "no proofs to anchor"}

    return {
        "merkle_root": root,
        "bitcoin_op_return": root[:80]
    }


# -------------------------
# explorer page
# -------------------------

@app.get("/explorer", response_class=HTMLResponse)
def explorer(request: Request):

    proofs = load_proofs()

    return templates.TemplateResponse(
        "explorer.html",
        {
            "request": request,
            "proofs": proofs
        }
    )

