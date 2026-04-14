from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import requests
import hashlib
import sqlite3
import qrcode
from io import BytesIO
import secrets
import os

app = FastAPI()

# ===== CONFIG =====
BLOCKCYPHER_API_KEY = os.getenv("e57d6275d53846259d6d46aca3981b6a")
MIN_PAYMENT_SATS = 10000   # 10k sats
FREE_LIMIT = 5

# ===== DB =====
conn = sqlite3.connect("db.sqlite", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    btc_address TEXT UNIQUE,
    premium INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT UNIQUE,
    btc_address TEXT,
    usage_count INTEGER DEFAULT 0
)
""")

conn.commit()

# ===== UTILS =====
def hash_data(data: str):
    return hashlib.sha256(data.encode()).hexdigest()

def generate_api_key():
    return "sk_" + secrets.token_hex(16)

def sats_to_btc(sats):
    return sats / 100_000_000

# ===== BTC =====
def create_btc_address():
    try:
        if not BLOCKCYPHER_API_KEY:
            return {"error": "Missing API key"}

        url = f"https://api.blockcypher.com/v1/btc/main/addrs?token={e57d6275d53846259d6d46aca3981b6a}"
        return requests.post(url).json()

    except Exception as e:
        return {"error": str(e)}

def get_balance(address):
    try:
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}"
        return requests.get(url).json().get("final_balance", 0)
    except:
        return 0

# ===== ROUTES =====

@app.get("/")
def home():
    return {"message": "🚀 Bitcoin SaaS LIVE"}

# 💳 paiement
@app.post("/pay")
def pay():
    wallet = create_btc_address()

    if "error" in wallet:
        return wallet

    address = wallet.get("address")
    if not address:
        raise HTTPException(status_code=500, detail="BTC error")

    api_key = generate_api_key()

    cursor.execute(
        "INSERT OR IGNORE INTO users (btc_address) VALUES (?)",
        (address,)
    )

    cursor.execute(
        "INSERT INTO api_keys (api_key, btc_address) VALUES (?, ?)",
        (api_key, address)
    )

    conn.commit()

    return {
        "btc_address": address,
        "api_key": api_key,
        "amount_sats": MIN_PAYMENT_SATS,
        "amount_btc": sats_to_btc(MIN_PAYMENT_SATS)
    }

# 🔔 check paiement
@app.get("/check/{address}")
def check(address: str):
    balance = get_balance(address)

    if balance >= MIN_PAYMENT_SATS:
        cursor.execute(
            "UPDATE users SET premium=1 WHERE btc_address=?",
            (address,)
        )
        conn.commit()

    cursor.execute(
        "SELECT premium FROM users WHERE btc_address=?",
        (address,)
    )
    user = cursor.fetchone()

    return {
        "paid": balance >= MIN_PAYMENT_SATS,
        "balance_sats": balance,
        "premium": bool(user[0]) if user else False
    }

# 🔐 API protégée
@app.post("/v1/proofs")
def proof(data: str, api_key: str):

    cursor.execute(
        "SELECT btc_address, usage_count FROM api_keys WHERE api_key=?",
        (api_key,)
    )
    key = cursor.fetchone()

    if not key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    address, usage = key

    cursor.execute(
        "SELECT premium FROM users WHERE btc_address=?",
        (address,)
    )
    user = cursor.fetchone()

    if user[0] == 0 and usage >= FREE_LIMIT:
        raise HTTPException(status_code=402, detail="Free limit reached")

    cursor.execute(
        "UPDATE api_keys SET usage_count = usage_count + 1 WHERE api_key=?",
        (api_key,)
    )
    conn.commit()

    return {"hash": hash_data(data)}

# 📊 dashboard
@app.get("/dashboard/{api_key}")
def dashboard(api_key: str):
    cursor.execute(
        "SELECT usage_count, btc_address FROM api_keys WHERE api_key=?",
        (api_key,)
    )
    data = cursor.fetchone()

    if not data:
        return {"error": "invalid key"}

    usage, address = data

    cursor.execute(
        "SELECT premium FROM users WHERE btc_address=?",
        (address,)
    )
    user = cursor.fetchone()

    return {
        "usage": usage,
        "premium": bool(user[0])
    }

# 📱 QR avec montant BTC
@app.get("/qr/{address}/{amount}")
def qr(address: str, amount: int):
    btc_amount = sats_to_btc(amount)
    uri = f"bitcoin:{address}?amount={btc_amount}"

    img = qrcode.make(uri)

    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

# 🌐 UI PRO BTC
@app.get("/app", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <body style="text-align:center;font-family:Arial;background:#0b0f1a;color:white">

    <h1>₿ Bitcoin Proof API</h1>
    <p>Free: 5 requests</p>
    <h2>Premium: <span id="btc"></span> BTC</h2>
    <p id="sats"></p>

    <button onclick="pay()" style="padding:10px 20px;background:#f7931a;border:none;color:white;font-size:16px;cursor:pointer;">
    Unlock Premium
    </button>

    <p id="addr"></p>
    <img id="qr" width="220"/>

    <p id="key"></p>
    <p id="status"></p>

    <script>
    let addr = null;
    let amount = null;

    async function pay(){
        let r = await fetch('/pay',{method:'POST'});
        let d = await r.json();

        if(d.error){
            document.getElementById('status').innerHTML = d.error;
            return;
        }

        addr = d.btc_address;
        amount = d.amount_sats;

        document.getElementById('addr').innerHTML = "Send BTC to: " + addr;
        document.getElementById('btc').innerHTML = d.amount_btc;
        document.getElementById('sats').innerHTML = d.amount_sats + " sats";

        document.getElementById('qr').src =
            '/qr/' + addr + '/' + amount;

        document.getElementById('key').innerHTML =
            "API KEY: " + d.api_key;
    }

    async function check(){
        if(!addr) return;

        let r = await fetch('/check/'+addr);
        let d = await r.json();

        document.getElementById('status').innerHTML =
            d.premium ? "✅ Premium unlocked" : "⏳ Waiting payment...";
    }

    setInterval(check,4000);
    </script>

    </body>
    </html>
    """