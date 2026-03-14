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

PROOF_FILE = "proofs.json"
API_KEY = os.getenv("API_KEY", "dev_key_123456")


# -------------------
# utils
# -------------------

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


# -------------------
# root page
# -------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# -------------------
# dashboard
# -------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    proofs = load_proofs()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "proofs": proofs
        }
    )


# -------------------
# explorer
# -------------------

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


# -------------------
# verify
# -------------------

@app.post("/verify")
async def verify(request: Request):

    key = request.headers.get("X-API-KEY")

    if key != API_KEY:
        return {"error": "unauthorized"}

    data = await request.json()

    message = data.get("message")
    address = data.get("address")
    signature = data.get("signature")

    if not message:
        return {"error": "message missing"}

    message_hash = sha256(message)

    proof = {

        "verification_id": str(uuid.uuid4())[:8],
        "message": message,
        "message_hash": message_hash,
        "address": address,
        "signature": signature,
        "timestamp": datetime.utcnow().isoformat()

    }

    proofs = load_proofs()
    proofs.append(proof)

    save_proofs(proofs)

    return proof


# -------------------
# proofs
# -------------------

@app.get("/proofs")
def proofs():

    data = load_proofs()

    return {
        "count": len(data),
        "proofs": data
    }


# -------------------
# single proof
# -------------------

@app.get("/proof/{verification_id}")
def proof(verification_id: str):

    proofs = load_proofs()

    for p in proofs:

        if p["verification_id"] == verification_id:
            return p

    return {"error": "proof not found"}


# -------------------
# merkle root
# -------------------

@app.get("/merkle")
def merkle():

    proofs = load_proofs()

    hashes = [p["message_hash"] for p in proofs]

    if len(hashes) == 0:
        return {"proof_count": 0, "merkle_root": None}

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

    return {

        "proof_count": len(hashes),
        "merkle_root": layer[0]

    }


# -------------------
# anchor
# -------------------

@app.get("/anchor")
def anchor():

    proofs = load_proofs()

    hashes = [p["message_hash"] for p in proofs]

    if len(hashes) == 0:
        return {"error": "no proofs"}

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

    root = layer[0]

    return {

        "merkle_root": root,
        "bitcoin_op_return": root[:80]

    }
@app.get("/anchor")
def anchor():

    proofs = load_proofs()

    hashes = [p["message_hash"] for p in proofs]

    if len(hashes) == 0:
        return {"error": "no proofs"}

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

    root = layer[0]

    return {
        "merkle_root": root,
        "bitcoin_op_return": root[:80]
    }