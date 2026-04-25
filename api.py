from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import requests

app = FastAPI()

BTC_ADDRESS = "1KLPFtzz5hkBeYpkYjSFUMiBx7yi9YTXy8"  # TON adresse
PRICE_BTC = 0.0001

payments = {}


def check_payment_received():
    try:
        url = f"https://blockstream.info/api/address/{BTC_ADDRESS}"
        r = requests.get(url)
        data = r.json()

        received_sats = data["chain_stats"]["funded_txo_sum"]
        return received_sats / 100_000_000
    except:
        return 0


@app.get("/")
def home():
    return {"status": "OK"}


@app.get("/pay")
def pay():
    api_key = "sk_" + str(uuid.uuid4())[:12]

    payments[api_key] = {
        "paid": False
    }

    return {
        "btc_address": BTC_ADDRESS,
        "amount_btc": PRICE_BTC,
        "api_key": api_key
    }


@app.get("/check/{api_key}")
def check(api_key: str):
    if api_key not in payments:
        return {"error": "not found"}

    received = check_payment_received()

    if received >= PRICE_BTC:
        payments[api_key]["paid"] = True

    return payments[api_key]


@app.get("/app", response_class=HTMLResponse)
def app_page():
    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">
        <h1>₿ Bitcoin API</h1>

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
                "<br><br><b>Your API Key:</b><br>" + d.api_key +
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