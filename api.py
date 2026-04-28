from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import requests
import bip32utils
import os
import qrcode
import base64
from io import BytesIO
from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)

    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )# ===== CONFIG =====
XPUB = "xpub6DRyLsBsY3pCnrRd9BSzrJp6rfGunGEuzDVMkRoKjuk4M1G9b8spxibBSe9eagCDp6ANVVR6u4HoTtPXUGbGNURMagwKBzvQcPtsHeixUyu"
PRICE_BTC = 0.0001

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ===== MODEL =====
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    api_key = Column(String, unique=True)
    address = Column(String)
    paid = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# ===== ADDRESS =====
def generate_address(index):
    key = bip32utils.BIP32Key.fromExtendedKey(XPUB)
    child = key.ChildKey(index)
    return child.Address()

def check_address(address):
    try:
        url = f"https://blockstream.info/api/address/{address}"
        r = requests.get(url)
        data = r.json()
        return data["chain_stats"]["funded_txo_sum"] / 100_000_000
    except:
        return 0
def check_address(address):
    try:
        url = f"https://blockstream.info/api/address/{address}"
        r = requests.get(url)
        data = r.json()
        return data["chain_stats"]["funded_txo_sum"] / 100_000_000
    except:
        return 0


# 👉 AJOUT ICI
def generate_qr(address, amount):
    uri = f"bitcoin:{address}?amount={amount}"

    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode()
# ===== ROUTES =====
@app.get("/")
def home():
    return {"status": "OK"}

@app.get("/pay")
def pay():
    db = SessionLocal()

    index = db.query(Payment).count()
    address = generate_address(index)
    api_key = "sk_" + str(uuid.uuid4())[:12]

    qr = generate_qr(address, PRICE_BTC)

    payment = Payment(api_key=api_key, address=address, paid=False)
    db.add(payment)
    db.commit()

    return {
        "btc_address": address,
        "amount_btc": PRICE_BTC,
        "order_id": api_key,
        "qr": qr
    }

@app.get("/check/{order_id}")
def check(order_id: str):
    db = SessionLocal()

    payment = db.query(Payment).filter_by(api_key=order_id).first()

    if not payment:
        return {"error": "not found"}

    received = check_address(payment.address)

    if received >= PRICE_BTC:
        payment.paid = True
        db.commit()

    if payment.paid:
        return {
            "paid": True,
            "api_key": payment.api_key
        }

    return {"paid": False}

# ===== UI =====
@app.get("/app", response_class=HTMLResponse)
def app_page():
    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;">
        <h1>₿ Bitcoin API</h1>
        <h2>{PRICE_BTC} BTC</h2>

        <button onclick="pay()">Unlock</button>

        <p id="result"></p>

        <script>
        let order = "";

        async function pay(){{
            let r = await fetch('/pay');
            let d = await r.json();

            order = d.order_id;

            document.getElementById('result').innerHTML =
                "Send BTC to:<br>" + d.btc_address +
                "<br><br>Amount: " + d.amount_btc + " BTC" +
                "<br><br><button onclick='check()'>Check Payment</button>";
        }}

        async function check(){{
            let r = await fetch('/check/' + order);
            let d = await r.json();

            if(d.paid){{
                document.getElementById('result').innerHTML +=
                    "<br><br>✅ Payment confirmed!" +
                    "<br><br>Your API Key:<br>" + d.api_key;
            }} else {{
                document.getElementById('result').innerHTML +=
                    "<br><br>⏳ Waiting payment...";
            }}
        }}
        </script>
    </body>
    </html>
    """

# ===== DASHBOARD =====
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(auth: HTTPBasicCredentials = Depends(check_auth)):
    db = SessionLocal()
    payments = db.query(Payment).all()

    rows = ""

    for p in payments:
        status = "PAID" if p.paid else "WAITING"
        rows += f"<tr><td>{p.api_key}</td><td>{p.address}</td><td>{status}</td></tr>"

    return f"""
    <html>
    <body style="background:black;color:white;">
        <h1>Dashboard</h1>
        <table border="1">
            <tr><th>API Key</th><th>Address</th><th>Status</th></tr>
            {rows}
        </table>
    </body>
    </html>
    """
