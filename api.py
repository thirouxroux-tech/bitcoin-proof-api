from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import requests
import bip32utils

app = FastAPI()

XPUB = "xpub6DRyLsBsY3pCnrRd9BSzrJp6rfGunGEuzDVMkRoKjuk4M1G9b8spxibBSe9eagCDp6ANVVR6u4HoTtPXUGbGNURMagwKBzvQcPtsHeixUyu"
PRICE_BTC = 0.0001

payments = {}
index_counter = 0


# 🔑 générer adresse unique depuis xpub
def generate_address(index):
    key = bip32utils.BIP32Key.fromExtendedKey(XPUB)
    child = key.ChildKey(index)
    return child.Address()


# 🔍 vérifier paiement sur une adresse
def check_address(address):
    try:
        url = f"https://blockstream.info/api/address/{address}"
        r = requests.get(url)
        data = r.json()

        received = data["chain_stats"]["funded_txo_sum"]
        return received / 100_000_000
    except:
        return 0


@app.get("/")
def home():
    return {"status": "OK"}


@app.get("/pay")
def pay():
    global index_counter

    api_key = "sk_" + str(uuid.uuid4())[:12]

    # 👉 nouvelle adresse unique
    address = generate_address(index_counter)
    index_counter += 1

    payments[api_key] = {
        "paid": False,
        "address": address
    }

    return {
        "btc_address": address,
        "amount_btc": PRICE_BTC,
        "api_key": api_key
    }


@app.get("/check/{api_key}")
def check(api_key: str):
    if api_key not in payments:
        return {"error": "not found"}

    address = payments[api_key]["address"]
    received = check_address(address)

    if received >= PRICE_BTC:
        payments[api_key]["paid"] = True

    return payments[api_key]


@app.get("/app", response_class=HTMLResponse)
def app_page():
    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">
        <h1>₿ Bitcoin API PRO</h1>

        <h2>Premium: {PRICE_BTC} BTC</h2>

        <button onclick="pay()">Unlock</button>

        <p id="result"></p>

        <script>
        let currentKey = "";

        async function pay(){{
            let r = await fetch('/pay');
            let d = await r.json();

            currentKey = d.api_key;

            document.getElementById('result').innerHTML =
                "<br><b>Send BTC to:</b><br>" + d.btc_address +
                "<br><br><b>Amount:</b> " + d.amount_btc + " BTC" +
                "<br><br><b>API Key:</b><br>" + d.api_key +
                "<br><br><button onclick='check()'>Check Payment</button>";
        }}

        async function check(){{
            let r = await fetch('/check/' + currentKey);
            let d = await r.json();

            if(d.paid){{
                document.getElementById('result').innerHTML += "<br><br>✅ Payment confirmed!";
            }} else {{
                document.getElementById('result').innerHTML += "<br><br>⏳ Waiting payment...";
            }}
        }}
        </script>
    </body>
    </html>
    """