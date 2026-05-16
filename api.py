from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse

import os
import uuid
import requests
import bip32utils
import qrcode
import base64

from io import BytesIO

from sqlalchemy import (
    create_engine,
    Column,
    String
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)

# ==================================================
# FASTAPI
# ==================================================

app = FastAPI()

# ==================================================
# CONFIG
# ==================================================

XPUB = "TON_XPUB_ICI"

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================================================
# DATABASE
# ==================================================

DATABASE_URL = "sqlite:///paywall.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class FileData(Base):

    __tablename__ = "files"

    id = Column(String, primary_key=True)

    filename = Column(String)

    price = Column(String)

    address = Column(String)

Base.metadata.create_all(bind=engine)

# ==================================================
# BTC ADDRESS
# ==================================================

def generate_address(index):

    key = bip32utils.BIP32Key.fromExtendedKey(XPUB)

    return key.ChildKey(index).Address()

# ==================================================
# QR CODE
# ==================================================

def generate_qr(address, amount):

    uri = f"bitcoin:{address}?amount={amount}"

    qr = qrcode.make(uri)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    return base64.b64encode(
        buffer.getvalue()
    ).decode()

# ==================================================
# CHECK BTC PAYMENT
# ==================================================

def check_payment(address, expected_amount):

    try:

        url = f"https://blockstream.info/api/address/{address}"

        data = requests.get(url).json()

        received = (
            data["chain_stats"]["funded_txo_sum"]
            / 100_000_000
        )

        return received >= float(expected_amount)

    except:

        return False

# ==================================================
# HOME
# ==================================================

@app.head("/")
def head_home():
    return

@app.get("/", response_class=HTMLResponse)
def home():

    print("HOME PAGE VISITED")

    return """

<!DOCTYPE html>
<html>

<head>

<title>LightningDrop</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body{
    margin:0;
    background:#0b0b0b;
    color:white;
    font-family:Arial;
}

.container{
    width:90%;
    max-width:1100px;
    margin:auto;
}

.hero{
    padding-top:80px;
    padding-bottom:80px;
    text-align:center;
}

.logo{
    font-size:22px;
    color:#f7931a;
    font-weight:bold;
    margin-bottom:40px;
}

h1{
    font-size:64px;
    margin-bottom:20px;
    line-height:1.1;
}

.subtitle{
    font-size:22px;
    color:#999;
    max-width:700px;
    margin:auto;
    margin-bottom:50px;
}

.card{
    background:#171717;
    padding:40px;
    border-radius:24px;
    max-width:500px;
    margin:auto;
}

input{
    width:100%;
    padding:16px;
    margin-bottom:20px;
    border-radius:12px;
    border:none;
    background:#222;
    color:white;
    box-sizing:border-box;
    font-size:16px;
}

button{
    width:100%;
    padding:18px;
    border:none;
    border-radius:14px;
    background:#f7931a;
    color:black;
    font-size:18px;
    font-weight:bold;
    cursor:pointer;
}

.steps{
    margin-top:120px;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
    gap:30px;
}

.step{
    background:#171717;
    padding:30px;
    border-radius:20px;
}

.step h3{
    color:#f7931a;
}

.footer{
    text-align:center;
    color:#666;
    padding:60px 0;
}

@media(max-width:700px){

    h1{
        font-size:42px;
    }

    .subtitle{
        font-size:18px;
    }

}

</style>

</head>

<body>

<div class="container">

    <div class="hero">

        <div class="logo">
        ⚡ LightningDrop
        </div>

        <h1>
        Instant Bitcoin Paywalls
        </h1>

        <div class="subtitle">
        Upload a file, set a Bitcoin price,
        and share your paywall instantly.
        </div>

        <div class="card">

            <form
            action="/create"
            method="post"
            enctype="multipart/form-data"
            >

                <input
                type="file"
                name="file"
                required
                >

                <input
                type="text"
                name="price"
                placeholder="Price in BTC"
                required
                >

                <button type="submit">
                Create Paywall
                </button>

            </form>

        </div>

        <div class="steps">

            <div class="step">
                <h3>1. Upload</h3>

                <p>
                Upload any digital file.
                </p>
            </div>

            <div class="step">
                <h3>2. Set Price</h3>

                <p>
                Choose your Bitcoin price instantly.
                </p>
            </div>

            <div class="step">
                <h3>3. Get Paid</h3>

                <p>
                Share your link and receive Bitcoin directly.
                </p>
            </div>

        </div>

    </div>

    <div class="footer">
    Powered by Bitcoin ⚡
    </div>

</div>

</body>

</html>

"""

# ==================================================
# CREATE PAYWALL
# ==================================================

@app.post("/create")
async def create(
    price: str = Form(...),
    file: UploadFile = File(...)
):

    db = SessionLocal()

    file_id = str(uuid.uuid4())[:8]

    filename = f"{file_id}_{file.filename}"

    filepath = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(filepath, "wb") as f:
        f.write(await file.read())

    address = generate_address(
        db.query(FileData).count()
    )

    new_file = FileData(

        id=file_id,

        filename=filename,

        price=price,

        address=address
    )

    db.add(new_file)

    db.commit()

    return HTMLResponse(f"""

    <html>

    <body style="
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:100px;
    ">

        <h1>✅ Paywall Created</h1>

        <p>
        Share this link:
        </p>

        <a
        href="/pay/{file_id}"
        style="
            color:#f7931a;
            font-size:22px;
        "
        >
        /pay/{file_id}
        </a>

    </body>

    </html>

    """)

# ==================================================
# PAY PAGE
# ==================================================

@app.get("/pay/{file_id}", response_class=HTMLResponse)
def pay(file_id: str):

    print("PAYWALL VISITED:", file_id)

    db = SessionLocal()

    data = db.query(FileData).filter_by(
        id=file_id
    ).first()

    if not data:
        return HTMLResponse("Not found")

    qr = generate_qr(
        data.address,
        data.price
    )

    return HTMLResponse(f"""

    <html>

    <body style="
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:60px;
    ">

        <h1>⚡ Bitcoin Payment</h1>

        <h2>{data.price} BTC</h2>

        <img
        width="250"
        src="data:image/png;base64,{qr}"
        >

        <p style="
            width:80%;
            margin:auto;
            margin-top:30px;
            color:#999;
            word-break:break-all;
        ">
        {data.address}
        </p>

        <br>

        <button
        onclick="checkPayment()"
        style="
            background:#f7931a;
            color:black;
            border:none;
            padding:16px 24px;
            border-radius:12px;
            font-size:18px;
            font-weight:bold;
            cursor:pointer;
        "
        >
        Check Payment
        </button>

        <div id="status"></div>

        <script>

        async function checkPayment(){

            let r = await fetch('/check/{file_id}')

            let d = await r.json()

            if(d.paid){
                document.getElementById('status').innerHTML = `
                    <br><br>

                    <a
                    href="/download/{file_id}"
                    style="
                        color:#f7931a;
                        font-size:24px;
                    "
                    >
                    Download File
                    </a>
                `
            }

            else {

                document.getElementById('status').innerHTML =
                "<br><br>⏳ Waiting payment..."

            }

        }

        </script>

    </body>

    </html>

    """)

# ==================================================
# CHECK PAYMENT
# ==================================================

@app.get("/check/{file_id}")
def check(file_id: str):

    db = SessionLocal()

    data = db.query(FileData).filter_by(
        id=file_id
    ).first()

    if not data:
        return {"paid": False}

    paid = check_payment(
        data.address,
        data.price
    )

    return {
        "paid": paid
    }

# ==================================================
# DOWNLOAD FILE
# ==================================================

@app.get("/download/{file_id}")
def download(file_id: str):

    db = SessionLocal()

    data = db.query(FileData).filter_by(
        id=file_id
    ).first()

    if not data:
        return {"error":"not found"}

    path = os.path.join(
        UPLOAD_DIR,
        data.filename
    )

    return FileResponse(path)