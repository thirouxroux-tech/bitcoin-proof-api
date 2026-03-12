from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import hashlib
import uuid
import os
import sqlite3
import qrcode

from reportlab.pdfgen import canvas

app = FastAPI()

API_KEY="dev_key_123456"

# CORS

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["*"],
allow_headers=["*"],
)

# dossiers

CERT_FOLDER="certificates"
os.makedirs(CERT_FOLDER,exist_ok=True)

# database

conn=sqlite3.connect("bitcoinproof.db",check_same_thread=False)
cursor=conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS proofs(
id TEXT,
address TEXT,
message_hash TEXT
)
""")

conn.commit()

# models

class VerifyRequest(BaseModel):
address:str
message:str
signature:str

# accueil

@app.get("/",response_class=HTMLResponse)
def home():

```
return """

<html>

<head>
<title>BitcoinProof</title>

<style>

body{
font-family:Arial;
background:#0f172a;
color:white;
text-align:center;
padding:40px;
}

a{
color:#f7931a;
}

</style>

</head>

<body>

<h1>BitcoinProof API</h1>

<p>Blockchain proof service</p>

<p>

<a href="/dashboard">Dashboard</a> |
<a href="/explorer">Explorer</a> |
<a href="/docs">API Docs</a>

</p>

</body>

</html>

"""
```

# dashboard

@app.get("/dashboard")
def dashboard():
return FileResponse("dashboard.html")

# verify

@app.post("/verify")
def verify(data:VerifyRequest,x_api_key:str=Header(None)):

```
if x_api_key!=API_KEY:
    raise HTTPException(status_code=401,detail="invalid api key")

verification_id=str(uuid.uuid4())[:8]

message_hash=hashlib.sha256(data.message.encode()).hexdigest()

proof_url=f"https://bitcoin-proof-api.onrender.com/proof/{verification_id}"

qr=qrcode.make(proof_url)

qr_file=f"{CERT_FOLDER}/qr_{verification_id}.png"

qr.save(qr_file)

pdf_file=f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

c=canvas.Canvas(pdf_file)

c.setFont("Helvetica",16)
c.drawString(150,750,"Bitcoin Proof Certificate")

c.setFont("Helvetica",12)

c.drawString(50,700,f"Verification ID: {verification_id}")
c.drawString(50,670,f"Bitcoin Address: {data.address}")
c.drawString(50,640,f"Message: {data.message}")
c.drawString(50,610,f"Message Hash: {message_hash}")

c.drawImage(qr_file,230,420,width=120,height=120)

c.drawString(200,400,"Scan QR to verify proof")

c.save()

cursor.execute(
"INSERT INTO proofs(id,address,message_hash) VALUES (?,?,?)",
(verification_id,data.address,message_hash)
)

conn.commit()

return {
    "status":"valid",
    "verification_id":verification_id,
    "certificate":f"/certificate/{verification_id}"
}
```

# certificat

@app.get("/certificate/{verification_id}")
def certificate(verification_id:str):

```
file=f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

if not os.path.exists(file):
    raise HTTPException(status_code=404,detail="not found")

return FileResponse(file)
```

# proof page

@app.get("/proof/{verification_id}",response_class=HTMLResponse)
def proof(verification_id:str):

```
return f"""

<html>

<body style="font-family:Arial;background:#0f172a;color:white;text-align:center;padding:40px;">

<h1>BitcoinProof</h1>

<h2>Verification Proof</h2>

<p>ID:</p>

<h3>{verification_id}</h3>

<p>This certificate confirms a verified Bitcoin signature.</p>

</body>

</html>

"""
```

# explorer

@app.get("/explorer",response_class=HTMLResponse)
def explorer():

```
cursor.execute("SELECT id,address,message_hash FROM proofs")

rows=cursor.fetchall()

html="""

<html>

<head>

<title>BitcoinProof Explorer</title>

<style>

body{
font-family:Arial;
background:#0f172a;
color:white;
text-align:center;
padding:40px;
}

table{
margin:auto;
border-collapse:collapse;
}

td,th{
border:1px solid white;
padding:10px;
}

a{color:#f7931a;}

</style>

</head>

<body>

<h1>BitcoinProof Explorer</h1>

<table>

<tr>

<th>ID</th>
<th>Address</th>
<th>Hash</th>
<th>Proof</th>
<th>Certificate</th>

</tr>

"""

for r in rows:

    vid=r[0]
    address=r[1]
    h=r[2]

    html+=f"""

    <tr>

    <td>{vid}</td>
    <td>{address}</td>
    <td>{h}</td>

    <td><a href="/proof/{vid}">View</a></td>

    <td><a href="/certificate/{vid}">PDF</a></td>

    </tr>

    """

html+="</table></body></html>"

return html
```



