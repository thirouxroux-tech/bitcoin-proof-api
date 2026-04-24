from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid

app = FastAPI()

# 👉 CONFIG BTC (MET TON ADRESSE ICI)
BTC_ADDRESS = "1EqFMsnyCxg5aa5VBF1xJcWRDpSfcArHWE"  # ⚠️ remplace par TON adresse

# 👉 Prix fixe en BTC
PRICE_BTC = 0.0001


@app.get("/")
def home():
    return {"status": "Bitcoin API OK"}


@app.get("/pay")
def pay():
    api_key = "sk_" + str(uuid.uuid4())[:12]

    return {
        "btc_address": BTC_ADDRESS,
        "amount_btc": PRICE_BTC,
        "api_key": api_key
    }


@app.get("/app", response_class=HTMLResponse)
def app_page():
    return f"""
    <html>
    <head>
        <title>Bitcoin API</title>
    </head>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">
        <h1>₿ Bitcoin API</h1>

        <p>Free: 5 requests</p>
        <h2>Premium: {PRICE_BTC} BTC</h2>

        <button onclick="pay()" style="padding:10px 20px;font-size:16px;background:orange;border:none;">
            Unlock Premium
        </button>

        <p id="result"></p>

        <script>
        async function pay(){{
            let r = await fetch('/pay');
            let d = await r.json();

            document.getElementById('result').innerHTML =
                "<br><b>Adresse BTC :</b><br>" + d.btc_address +
                "<br><br><b>Montant :</b> " + d.amount_btc + " BTC" +
                "<br><br><b>API Key :</b><br>" + d.api_key;
        }}
        </script>
    </body>
    </html>
    """