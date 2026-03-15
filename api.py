from fastapi import FastAPI, Request, Header
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

API_KEY = "dev_key_123456"


# -------------------------
# helpers
# -------------------------

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


def load_proofs():

    if not os.path.exists(PROOF_FILE):
        return []

    with open(PROOF_FILE, "r") as f:
        return json.load(f)


def save_proofs(proofs):

    with open(PROOF_FILE, "w") as f:
        json.dump(proofs, f, indent=2)


# -------------------------
# root
# -------------------------

@app.get("/")
def root():

    return {"status": "Bitcoin Proof API running"}


# -------------------------
# verify proof
# -------------------------

@app.post("/verify")
async def verify(data: dict, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        return {"error": "invalid api key"}

    message = data.get("message")

    if not message:
        return {"error": "no message"}

    message_hash = sha256(message)

    verification_id = str(uuid.uuid4())[:8]

    proof = {

        "verification_id": verification_id,
        "message": message,
        "message_hash": message_hash,
        "timestamp": datetime.utcnow().isoformat()

    }

    proofs = load_proofs()

    proofs.append(proof)

    save_proofs(proofs)

    return proof


# -------------------------
# list proofs
# -------------------------

@app.get("/proofs")
def get_proofs():

    proofs = load_proofs()

    return {

        "count": len(proofs),
        "proofs": proofs

    }


# -------------------------
# get single proof
# -------------------------

@app.get("/proof/{verification_id}")
def get_proof(verification_id: str):

    proofs = load_proofs()

    for p in proofs:
        if p["verification_id"] == verification_id:
            return p

    return {"error": "proof not found"}


# -------------------------
# merkle tree
# -------------------------

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

            new_layer.append(sha256(left + right))

        layer = new_layer

    return {

        "proof_count": len(hashes),
        "merkle_root": layer[0]

    }


# -------------------------
# anchor (bitcoin root)
# -------------------------

@app.get("/anchor")
def anchor():

    result = merkle()

    root = result["merkle_root"]

    if not root:
        return {"error": "no proofs"}

    return {

        "merkle_root": root,
        "bitcoin_op_return": root[:80]

    }


# -------------------------
# merkle proof
# -------------------------

@app.get("/merkle-proof/{verification_id}")
def merkle_proof(verification_id: str):

    proofs = load_proofs()

    target = None

    for p in proofs:
        if p["verification_id"] == verification_id:
            target = p
            break

    if target is None:
        return {"error": "proof not found"}

    hashes = [p["message_hash"] for p in proofs]

    index = hashes.index(target["message_hash"])

    proof_path = []

    layer = hashes

    while len(layer) > 1:

        new_layer = []

        for i in range(0, len(layer), 2):

            left = layer[i]

            if i + 1 < len(layer):
                right = layer[i + 1]
            else:
                right = left

            if i == index or i + 1 == index:

                sibling = right if i == index else left

                proof_path.append(sibling)

                index = len(new_layer)

            new_hash = sha256(left + right)

            new_layer.append(new_hash)

        layer = new_layer

    return {

        "verification_id": verification_id,
        "merkle_root": layer[0],
        "merkle_proof": proof_path

    }


# -------------------------
# explorer page
# -------------------------

@app.get("/explorer", response_class=HTMLResponse)
def explorer(request: Request):

    proofs = load_proofs()

    return templates.TemplateResponse(

        "explorer.html",
        {"request": request, "proofs": proofs}

    )


# -------------------------
# dashboard page
# -------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    proofs = load_proofs()

    return templates.TemplateResponse(

        "dashboard.html",
        {"request": request, "proofs": proofs}

    )