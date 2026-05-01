from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import requests
import bip32utils
import qrcode
import base64
from io import BytesIO

app = FastAPI()

# ===== CONFIG =====
XPUB = "xpub6DRyLsBsY3pCnrRd9BSzrJp6rfGunGEuzDVMkRoKjuk4M1G9b8spxibBSe9eagCDp6ANVVR6u4HoTtPXUGbGNURMagwKBzvQcPtsHeixUyu"
PRICE_DEFAULT = 0.0001

payments = {}

# ===== BTC =====
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

def generate_qr(address, amount):
    uri = f"bitcoin:{address}?amount={amount}"
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# ===== HOME =====
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">

        <h1>₿ Bitcoin Payment Link</h1>

        <p>Create a Bitcoin payment link in seconds</p>
        <p>No signup. No KYC.</p>

        <input id="amount" placeholder="Amount in BTC (ex: 0.0001)" style="padding:10px;">
        <br><br>

        <button onclick="create()" style="padding:15px;font-size:18px;">
        🚀 Generate Payment Link
        </button>

        <p id="result"></p>

        <script>
        async function create(){
            let amount = document.getElementById('amount').value || "0.0001";

            let r = await fetch('/create?amount=' + amount);
            let d = await r.json();

            document.getElementById('result').innerHTML =
                "<br>Your link:<br><a href='/pay/" + d.id + "' target='_blank'>"
                + window.location.origin + "/pay/" + d.id + "</a>";
        }
        </script>

    </body>
    </html>
    """

# ===== CREATE LINK =====
@app.get("/create")
def create(amount: float = PRICE_DEFAULT):
    index = len(payments)
    address = generate_address(index)
    payment_id = str(uuid.uuid4())[:8]

    payments[payment_id] = {
        "address": address,
        "amount": amount,
        "paid": False
    }

    return {"id": payment_id}

# ===== PAYMENT PAGE =====
@app.get("/pay/{payment_id}", response_class=HTMLResponse)
def pay_page(payment_id: str):
    if payment_id not in payments:
        return "Not found"

    p = payments[payment_id]
    qr = generate_qr(p["address"], p["amount"])

    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">

        <h1>₿ Payment</h1>

        <p>Send BTC to:</p>
        <p>{p["address"]}</p>

        <h2>{p["amount"]} BTC</h2>

        <img width="200" src="data:image/png;base64,{qr}">

        <br><br>

        <button onclick="check()">Check Payment</button>

        <p id="status"></p>

        <script>
        async function check(){{
            let r = await fetch('/check/{payment_id}');
            let d = await r.json();

            if(d.paid){{
                document.getElementById('status').innerHTML = "✅ Payment received!";
            }} else {{
                document.getElementById('status').innerHTML = "⏳ Waiting payment...";
            }}
        }}
        </script>

    </body>
    </html>
    """

# ===== CHECK =====
@app.get("/check/{payment_id}")
def check(payment_id: str):
    if payment_id not in payments:
        return {"error": "not found"}

    p = payments[payment_id]

    received = check_address(p["address"])

    if received >= p["amount"]:
        p["paid"] = True

    return {"paid": p["paid"]}