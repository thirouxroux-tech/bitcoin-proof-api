from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import hashlib
import uuid
import os
import subprocess
import qrcode
import sqlite3

from bitcoin.signmessage import VerifyMessage, BitcoinMessage
from bitcoin.wallet import CBitcoinAddress
from reportlab.pdfgen import canvas

app = FastAPI()

# CORS

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

# DATABASE

conn = sqlite3.connect("bitcoinproof.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT UNIQUE,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS proofs(
id TEXT,
address TEXT,
message_hash TEXT,
user_id INTEGER
)
""")

conn.commit()

class VerifyRequest(BaseModel):
address: str
message: str
signature: str
user_id: int | None = None

class UserRegister(BaseModel):
email: str
password: str

class UserLogin(BaseModel):
email: str
password: str

@app.get("/")
def root():
return {"status": "Bitcoin Proof API running"}

@app.post("/register")
def register(user: UserRegister):

```
try:

    cursor.execute(
        "INSERT INTO users(email,password) VALUES (?,?)",
        (user.email, user.password)
    )

    conn.commit()

    return {"status": "user created"}

except:

    return {"status": "email already exists"}
```

@app.post("/login")
def login(user: UserLogin):

```
cursor.execute(
    "SELECT id FROM users WHERE email=? AND password=?",
    (user.email, user.password)
)

result = cursor.fetchone()

if result:

    return {
        "status": "login success",
        "user_id": result[0]
    }

return {"status": "invalid login"}
```

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

    qr = qrcode.make(proof_url)

    qr_path = f"{CERT_FOLDER}/qr_{verification_id}.png"
    qr.save(qr_path)

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

    try:
        subprocess.run(["ots", "stamp", pdf_file])
    except:
        pass

    cursor.execute(
        "INSERT INTO proofs(id,address,message_hash,user_id) VALUES (?,?,?,?)",
        (verification_id, data.address, message_hash, data.user_id)
    )

    conn.commit()

    return {
        "status": "valid",
        "verification_id": verification_id,
        "message_hash": message_hash,
        "certificate": f"/certificate/{verification_id}"
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

@app.get("/verify_timestamp/{verification_id}")
def verify_timestamp(verification_id: str):

```
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
```

@app.get("/user_proofs/{user_id}")
def user_proofs(user_id: int):

```
cursor.execute(
    "SELECT id,address,message_hash FROM proofs WHERE user_id=?",
    (user_id,)
)

rows = cursor.fetchall()

proofs = []

for r in rows:

    proofs.append({
        "verification_id": r[0],
        "address": r[1],
        "message_hash": r[2]
    })

return proofs
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

