from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import hashlib, sqlite3, secrets, qrcode
from io import BytesIO

app = FastAPI()

# ===== CONFIG =====
MIN_PAYMENT_SATS = 10000
FREE_LIMIT = 5

# ===== DB =====
conn = sqlite3.connect("db.sqlite", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    btc_address TEXT PRIMARY KEY,
    premium INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS api_keys (
    api_key TEXT PRIMARY KEY,
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

# ===== ROUTES =====

@app.get("/")
def home():
    return {"message": "Bitcoin SaaS LIVE"}

# 💳 paiement simulé (simple pour tester)
@app.get("/pay")
def pay():
    address = "bc1qtestaddress123"  # FAKE pour test

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

# 🔐 API
@app.post("/v1/proofs")
def proof(data: str, api_key: str):

    cursor.execute(
        "SELECT usage_count FROM api_keys WHERE api_key=?",
        (api_key,)
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(403, "Invalid API key")

    usage = row[0]

    if usage >= FREE_LIMIT:
        raise HTTPException(402, "Free limit reached")

    cursor.execute(
        "UPDATE api_keys SET usage_count = usage_count + 1 WHERE api_key=?",
        (api_key,)
    )
    conn.commit()

    return {"hash": hash_data(data)}

# 📱 QR
@app.get("/qr/{address}")
def qr(address: str):
    img = qrcode.make(address)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# 🌐 UI
@app.get("/app", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <body style="background:#0b0f1a;color:white;text-align:center;font-family:Arial">

    <h1>₿ Bitcoin API</h1>
    <p>Free: 5 requests</p>
    <h2>Premium: <span id="btc"></span> BTC</h2>
    <p id="sats"></p>

    <button onclick="pay()">Unlock</button>

    <p id="addr"></p>
    <img id="qr" width="200"/>
    <p id="key"></p>

    <script>
    async function pay(){
        let r = await fetch('/pay',{method:'POST'});
        let d = await r.json();

        document.getElementById('addr').innerHTML = d.btc_address;
        document.getElementById('btc').innerHTML = d.amount_btc;
        document.getElementById('sats').innerHTML = d.amount_sats + " sats";
        document.getElementById('qr').src = '/qr/'+d.btc_address;
        document.getElementById('key').innerHTML = d.api_key;
    }
    </script>

    </body>
    </html>
    """