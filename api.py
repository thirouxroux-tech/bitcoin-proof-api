from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import hashlib
import uuid
import os
import sqlite3
import qrcode
import subprocess
import threading
import time

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

API_KEY="dev_key_123456"

CERT_FOLDER="certificates"
os.makedirs(CERT_FOLDER,exist_ok=True)

# DATABASE

conn=sqlite3.connect("bitcoinproof.db",check_same_thread=False)
cursor=conn.cursor()

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

# MERKLE SYSTEM

pending_hashes=[]

def merkle_root(hashes):

```
if len(hashes)==1:
    return hashes[0]

new_hashes=[]

for i in range(0,len(hashes),2):

    left=hashes[i]

    if i+1<len(hashes):
        right=hashes[i+1]
    else:
        right=left

    combined=hashlib.sha256((left+right).encode()).hexdigest()

    new_hashes.append(combined)

return merkle_root(new_hashes)
```

def anchor_merkle():

```
while True:

    time.sleep(600)

    if len(pending_hashes)==0:
        continue

    root=merkle_root(pending_hashes)

    filename="merkle_root.txt"

    with open(filename,"w") as f:
        f.write(root)

    try:
        subprocess.run(["ots","stamp",filename])
    except:
        pass

    print("Merkle anchored:",root)

    pending_hashes.clear()
```

threading.Thread(target=anchor_merkle,daemon=True).start()

# MODELS

class VerifyRequest(BaseModel):
address:str
message:str
signature:str
user_id:int|None=None

class UserRegister(BaseModel):
email:str
password:str

class UserLogin(BaseModel):
email:str
password:str

# ROOT

@app.get("/")
def root():
return {"status":"BitcoinProof API running"}

# REGISTER

@app.post("/register")
def register(user:UserRegister):

```
try:

    cursor.execute(
    "INSERT INTO users(email,password) VALUES (?,?)",
    (user.email,user.password)
    )

    conn.commit()

    return {"status":"user created"}

except:

    return {"status":"email exists"}
```

# LOGIN

@app.post("/login")
def login(user:UserLogin):

```
cursor.execute(
"SELECT id FROM users WHERE email=? AND password=?",
(user.email,user.password)
)

result=cursor.fetchone()

if result:

    return {
    "status":"login success",
    "user_id":result[0]
    }

return {"status":"invalid login"}
```

# VERIFY BITCOIN SIGNATURE

@app.post("/verify")
def verify(data:VerifyRequest,x_api_key:str=Header(None)):

```
if x_api_key!=API_KEY:
    raise HTTPException(status_code=401,detail="Invalid API key")

try:

    message=BitcoinMessage(data.message)

    verified=VerifyMessage(
    CBitcoinAddress(data.address),
    message,
    data.signature
    )

    if not verified:
        return {"status":"invalid"}

    verification_id=str(uuid.uuid4())[:8]

    message_hash=hashlib.sha256(data.message.encode()).hexdigest()

    pending_hashes.append(message_hash)

    proof_url=f"https://bitcoin-proof-api.onrender.com/proof/{verification_id}"

    qr=qrcode.make(proof_url)

    qr_path=f"{CERT_FOLDER}/qr_{verification_id}.png"

    qr.save(qr_path)

    pdf_file=f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

    c=canvas.Canvas(pdf_file)

    c.setFont("Helvetica",16)
    c.drawString(160,750,"Bitcoin Proof Certificate")

    c.setFont("Helvetica",12)

    c.drawString(50,700,f"Verification ID: {verification_id}")
    c.drawString(50,670,f"Bitcoin Address: {data.address}")
    c.drawString(50,640,f"Message: {data.message}")
    c.drawString(50,610,f"Message Hash: {message_hash}")

    c.drawImage(qr_path,230,420,width=120,height=120)

    c.drawString(200,400,"Scan to verify proof")

    c.save()

    cursor.execute(
    "INSERT INTO proofs(id,address,message_hash,user_id) VALUES (?,?,?,?)",
    (verification_id,data.address,message_hash,data.user_id)
    )

    conn.commit()

    return {
    "status":"valid",
    "verification_id":verification_id,
    "message_hash":message_hash,
    "certificate":f"/certificate/{verification_id}"
    }

except Exception as e:

    return {"status":"error","detail":str(e)}
```

# USER PROOFS

@app.get("/user_proofs/{user_id}")
def user_proofs(user_id:int):

```
cursor.execute(
"SELECT id,address,message_hash FROM proofs WHERE user_id=?",
(user_id,)
)

rows=cursor.fetchall()

result=[]

for r in rows:

    result.append({
    "verification_id":r[0],
    "address":r[1],
    "message_hash":r[2]
    })

return result
```

# DOWNLOAD CERTIFICATE

@app.get("/certificate/{verification_id}")
def certificate(verification_id:str):

```
pdf_file=f"{CERT_FOLDER}/certificate_{verification_id}.pdf"

if not os.path.exists(pdf_file):
    raise HTTPException(status_code=404,detail="Certificate not found")

return FileResponse(pdf_file)
```

# PUBLIC PROOF PAGE

@app.get("/proof/{verification_id}",response_class=HTMLResponse)
def proof(verification_id:str):

```
return f"""
```

<html>

<head>

<title>BitcoinProof</title>

<style>

body{{
font-family:Arial;
background:#0f172a;
color:white;
text-align:center;
padding:40px;
}}

.box{{
background:#1e293b;
padding:30px;
border-radius:10px;
width:500px;
margin:auto;
}}

h1{{color:#f7931a;}}

</style>

</head>

<body>

<div class="box">

<h1>BitcoinProof</h1>

<h2>Verification Proof</h2>

<p>ID:</p>

<h3>{verification_id}</h3>

<p>This certificate confirms a verified Bitcoin signature.</p>

</div>

</body>

</html>

"""


