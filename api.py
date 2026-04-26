from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import requests
import bip32utils
import os

from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Unauthorized")
app = FastAPI()

# ===== CONFIG =====
XPUB = "xpub6DRyLsBsY3pCnrRd9BSzrJp6rfGunGEuzDVMkRoKjuk4M1G9b8spxibBSe9eagCDp6ANVVR6u4HoTtPXUGbGNURMagwKBzvQcPtsHeixUyu"
PRICE_BTC = 0.0001

DATABASE_URL = os.getenv("DATABASE_URL")

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

    payment = Payment(api_key=api_key, address=address, paid=False)
    db.add(payment)
    db.commit()

  return {
    "btc_address": address,
    "amount_btc": PRICE_BTC,
    "order_id": api_key
}

@app.get("/check/{api_key}")
def check(api_key: str):
    db = SessionLocal()

    payment = db.query(Payment).filter_by(api_key=api_key).first()

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

# ===== APP =====
@app.get("/app", response_class=HTMLResponse)
def app_page():
    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;">
        <h1>₿ Bitcoin API</h1>
        <button onclick="pay()">Unlock</button>
        <p id="result"></p>

        <script>
        let key = "";

        <script>
let currentKey = "";

async function pay(){
    let r = await fetch('/pay');
    let d = await r.json();

    currentKey = d.order_id;

    document.getElementById('result').innerHTML =
        "<br><b>Send BTC to:</b><br>" + d.btc_address +
        "<br><br><b>Amount:</b> " + d.amount_btc + " BTC" +
        "<br><br><button onclick='check()'>Check Payment</button>";
}

async function check(){
    let r = await fetch('/check/' + currentKey);
    let d = await r.json();

    if(d.paid){
        document.getElementById('result').innerHTML += 
            "<br><br>✅ Payment confirmed!" +
            "<br><br><b>Your API Key:</b><br>" + d.api_key;
    } else {
        document.getElementById('result').innerHTML += 
            "<br><br>⏳ Waiting payment...";
    }
}
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