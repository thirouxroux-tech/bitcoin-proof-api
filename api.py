from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import hashlib
import uuid
import os
import qrcode
import subprocess

from bitcoin.signmessage import VerifyMessage, BitcoinMessage
from bitcoin.wallet import CBitcoinAddress

from reportlab.pdfgen import canvas

app = FastAPI()

# CORS (permet au site web d'appeler l'API)

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

API_KEY = "dev_key_123456"

CERT_FOLDER = "certificates"

os.makedirs(CERT_FOLDER, exist_ok=True)

# base mémoire simple pour les preuves

proofs_db = []

class VerifyRequest(BaseModel):
address: str
message: str
signature: str

@app.get("/")
def root():
return {"status": "Bitcoin Proof API running"}

@app.post("/verify")
def verify_signature(data: VerifyRequest, x_api_key: str = Header(None)):

```
if x_api_key != API_KEY:
    raise HTTPException(status_code=401, detail="Invalid API key")

try:

    message = BitcoinMessage(data.message)

    verified = VerifyMessage(
        CBitcoinAddress(data.address),
        message,
        data.signature
    )

    if not verified:
        return {"status": "invalid"}

    verification_id = str(uuid.uuid4())[:8]

    message_hash = hashlib.sha256(data.message.encode()).hexdigest()

    proof_url = f"https://bitcoin-proof-api.onrender.com/proof/{verification_id}"

    # génération QR code

    qr = qrcode.make(proof_url)

    qr_path = f"{CERT_FOLDER}/qr_{verification_id}.png"

    qr.save(qr_path)

    # génération certificat PDF

    pdf_file = f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont("Helvetica", 16)
    c.drawString(150, 750, "Bitcoin Proof Certificate")

    c.setFont("Helvetica", 12)

    c.drawString(50, 700, f"Verification ID: {verification_id}")
    c.drawString(50, 670, f"Bitcoin Address: {data.address}")
    c.drawString(50, 640, f"Message: {data.message}")
    c.drawString(50, 610, f"Message Hash: {message_hash}")

    c.drawImage(qr_path, 230, 420, width=120, height=120)

    c.drawString(200, 400, "Scan to verify this proof")

    c.save()
# ancrage OpenTimestamps (Bitcoin)

timestamp_file = pdf_file + ".ots"

try:
    subprocess.run([
        "ots",
        "stamp",
        pdf_file
    ])
except:
    pass
    # sauvegarde dans l'explorateur

    proofs_db.append({
        "id": verification_id,
        "address": data.address,
        "message_hash": message_hash
    })

 return {
    "status": "valid",
    "type": "Legacy (P2PKH)",
    "verification_id": verification_id,
    "message_hash": message_hash,
    "certificate_file": f"/certificate/{verification_id}",
    "timestamp_proof": f"/timestamp/{verification_id}"
}

except Exception as e:

    return {"status": "error", "detail": str(e)}
```

@app.get("/certificate/{verification_id}")
def get_certificate(verification_id: str):

```
pdf_file = f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

if not os.path.exists(pdf_file):
    raise HTTPException(status_code=404, detail="Certificate not found")

return FileResponse(pdf_file)
```

@app.get("/proof/{verification_id}", response_class=HTMLResponse)
def view_proof(verification_id: str):

```
return f"""
<html>

<head>

<title>BitcoinProof Verification</title>

<style>

body {{
    font-family: Arial;
    background:#0f172a;
    color:white;
    text-align:center;
    padding:40px;
}}

.box {{
    background:#1e293b;
    padding:30px;
    border-radius:10px;
    width:500px;
    margin:auto;
}}

h1 {{
    color:#f7931a;
}}

</style>

</head>

<body>

<div class="box">

<h1>BitcoinProof</h1>

<h2>Verification Proof</h2>

<p>Verification ID :</p>

<h3>{verification_id}</h3>

<p>This certificate confirms that a Bitcoin signed message was verified.</p>

</div>

</body>

</html>
"""
```

@app.get("/proofs", response_class=HTMLResponse)
def list_proofs():

```
html = """
<html>

<head>

<title>BitcoinProof Explorer</title>

<style>

body{
font-family:Arial;
background:#0f172a;
color:white;
padding:40px;
}

table{
width:100%;
border-collapse:collapse;
}

th,td{
padding:10px;
border-bottom:1px solid #333;
}

th{
color:#f7931a;
}

a{
color:#22c55e;
}

</style>

</head>

<body>

<h1>BitcoinProof Explorer</h1>

<table>

<tr>
<th>ID</th>
<th>Address</th>
<th>Message Hash</th>
<th>Proof</th>
<th>Certificate</th>
</tr>
"""

for p in proofs_db:

    html += f"""
    <tr>

    <td>{p['id']}</td>

    <td>{p['address']}</td>

    <td>{p['message_hash']}</td>

    <td>
    <a href="/proof/{p['id']}">view</a>
    </td>

    <td>
    <a href="/certificate/{p['id']}">download</a>
    </td>

    </tr>
    """

html += """
</table>

</body>

</html>
"""

return html
```
@app.get("/verify_timestamp/{verification_id}")
def verify_timestamp(verification_id: str):

    ots_file = f"{CERT_FOLDER}/certificate_{verification_id}.pdf.ots"

    if not os.path.exists(ots_file):
        return {"status": "no timestamp yet"}

    try:

        result = subprocess.run(
            ["ots", "verify", ots_file],
            capture_output=True,
            text=True
        )

        return {
            "verification_id": verification_id,
            "result": result.stdout
        }

    except Exception as e:

        return {"error": str(e)}

