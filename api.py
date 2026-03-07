from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from bitcoin.signmessage import VerifyMessage, BitcoinMessage
from bitcoin.wallet import CBitcoinAddress
import hashlib
import os
from datetime import datetime
from reportlab.pdfgen import canvas

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
API_KEY = os.getenv("API_KEY", "dev_key_123456")

class VerifyRequest(BaseModel):
    address: str
    message: str
    signature: str

def generate_certificate(data, verification_id):
    filename = f"certificate_{verification_id}.pdf"

    c = canvas.Canvas(filename)
    c.setFont("Helvetica", 12)

    c.drawString(100, 750, "Bitcoin Proof Certificate")
    c.drawString(100, 720, f"Verification ID: {verification_id}")
    c.drawString(100, 700, f"Address: {data['address']}")
    c.drawString(100, 680, f"Message: {data['message']}")
    c.drawString(100, 660, f"Status: {data['status']}")
    c.drawString(100, 640, f"Timestamp: {data['timestamp']}")
    c.drawString(100, 620, f"Message Hash: {data['message_hash']}")

    c.save()

    return filename

@app.get("/")
def root():
    return {"status": "Bitcoin Proof API running"}

@app.post("/verify")
def verify_signature(req: VerifyRequest, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        message = BitcoinMessage(req.message)
        address = CBitcoinAddress(req.address)

        valid = VerifyMessage(address, message, req.signature)

        message_hash = hashlib.sha256(req.message.encode()).hexdigest()

        addr_type = "Unknown"

        if req.address.startswith("1"):
            addr_type = "Legacy (P2PKH)"
        elif req.address.startswith("3"):
            addr_type = "P2SH"
        elif req.address.startswith("bc1"):
            addr_type = "SegWit"

        verification_id = hashlib.sha256(
            (req.address + req.message + req.signature).encode()
        ).hexdigest()[:8]

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        status = "valid" if valid else "invalid"

        data = {
            "address": req.address,
            "message": req.message,
            "status": status,
            "timestamp": timestamp,
            "message_hash": message_hash
        }

        certificate_file = generate_certificate(data, verification_id)

        return {
            "status": status,
            "type": addr_type,
            "timestamp": timestamp,
            "message_hash": message_hash,
            "verification_id": verification_id,
            "certificate_file": certificate_file
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))