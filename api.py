from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests
import uuid

app = FastAPI()

# ===== CONFIG BTCPAY =====
BTCPAY_URL = "https://mainnet.demo.btcpayserver.org"
STORE_ID = "HC6dTjE8vWsp2FQG17KvdVeSdrHNRHsuqLiydZEVpEbV"
API_KEY = "kkRE7L717d7URYhoGD1RDL00Z7vCEhChoYB71PM7lb7"

# stockage simple
payments = {}

PRICE_EUR = 5


@app.get("/")
def home():
    return {"status": "OK"}


# ===== CREATE PAYMENT =====
@app.get("/pay")
def pay():
    order_id = str(uuid.uuid4())

    url = f"{BTCPAY_URL}/api/v1/stores/{STORE_ID}/invoices"

    headers = {
        "Authorization": f"token {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "amount": PRICE_EUR,
        "currency": "EUR",
        "metadata": {
            "orderId": order_id
        }
    }

    r = requests.post(url, json=data, headers=headers)
    invoice = r.json()

    payments[order_id] = {
        "paid": False,
        "api_key": None
    }

    return {
        "checkout_url": invoice.get("checkoutLink"),
        "order_id": order_id
    }


# ===== WEBHOOK =====
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    event = data.get("type")

    if event == "InvoiceSettled":
        api_key = "sk_" + str(uuid.uuid4())[:12]

        print("✅ PAIEMENT CONFIRMÉ")
        print("🔑 API KEY:", api_key)

    return {"status": "ok"}


# ===== UI =====
@app.get("/app", response_class=HTMLResponse)
def app_page():
    return """
    <html>
    <body style="background:black;color:white;text-align:center;font-family:Arial;">
        <h1>₿ Bitcoin API</h1>

        <h2>Premium Access</h2>

        <button onclick="pay()">Pay with Bitcoin</button>

        <p id="result"></p>

        <script>
        async function pay(){
            let r = await fetch('/pay');
            let d = await r.json();

            window.location.href = d.checkout_url;
        }
        </script>
    </body>
    </html>
    """