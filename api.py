from sqlalchemy import (
    create_engine,
    Column,
    String
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse

import os
import uuid
import requests
import bip32utils
import qrcode
import base64

from io import BytesIO

app = FastAPI()
# ==================================================
# DATABASE
# ==================================================

DATABASE_URL = "sqlite:///paywall.db"

engine = create_engine(DATABASE_URL)

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
# CONFIG
# ==================================================

XPUB = "xpub6DRyLsBsY3pCnrRd9BSzrJp6rfGunGEuzDVMkRoKjuk4M1G9b8spxibBSe9eagCDp6ANVVR6u4HoTtPXUGbGNURMagwKBzvQcPtsHeixUyu"

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


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
# HOME
# ==================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """

    <!DOCTYPE html>
    <html>

    <head>

    <title>LightningDrop</title>

    <style>

    body{
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        margin:0;
    }

    .card{
        background:#171717;
        padding:40px;
        border-radius:20px;
        width:420px;
        text-align:center;
    }

    h1{
        font-size:40px;
    }

    p{
        color:#999;
        margin-bottom:30px;
    }

    input{
        width:100%;
        padding:14px;
        margin-bottom:20px;
        border-radius:10px;
        border:none;
        background:#222;
        color:white;
    }

    button{
        background:#f7931a;
        color:black;
        border:none;
        padding:16px;
        width:100%;
        border-radius:12px;
        font-size:18px;
        cursor:pointer;
        font-weight:bold;
    }

    </style>

    </head>

    <body>

        <div class="card">

            <h1>⚡ LightningDrop</h1>

            <p>
            Sell digital files with Bitcoin
            </p>

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

    file_id = str(uuid.uuid4())[:8]

    filename = f"{file_id}_{file.filename}"

    filepath = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(filepath, "wb") as f:
        f.write(await file.read())

    address = generate_address(
        len(FILES_DB)
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
db = SessionLocal()
    </body>

    </html>

    """)

# ==================================================
# PAY PAGE
# ==================================================

@app.get("/pay/{file_id}", response_class=HTMLResponse)
def pay(file_id: str):

    if file_id not in FILES_DB:
        return HTMLResponse("Not found")

    data = FILES_DB[file_id]

    qr = generate_qr(
        data["address"],
        data["price"]
    )
db = SessionLocal()
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

        <h2>{data["price"]} BTC</h2>

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
        {data["address"]}
        </p>

        <br><br>

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

        async function checkPayment(){{

            let r = await fetch('/check/{file_id}')

            let d = await r.json()

            if(d.paid){{
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
            }}

            else {{

                document.getElementById('status').innerHTML =
                "<br><br>⏳ Waiting payment..."

            }}

        }}

        </script>

    </body>

    </html>

    """)
# ==================================================
# CHECK ROUTE
# ==================================================

@app.get("/check/{file_id}")
def check(file_id: str):

    data = db.query(FileData).filter_by(id=file_id).first()

if not data:
        return {"paid": False}

    

    paid = check_payment(
        data["address"],
        data["price"]
    )

    return {
        "paid": paid
    }

# ==================================================
# DOWNLOAD FILE
# ==================================================

@app.get("/download/{file_id}")
def download(file_id: str):

    if file_id not in FILES_DB:
        return {"error":"not found"}

    data = FILES_DB[file_id]

    path = os.path.join(
        UPLOAD_DIR,
        data["filename"]
    )

    from fastapi.responses import FileResponse

    return FileResponse(path)