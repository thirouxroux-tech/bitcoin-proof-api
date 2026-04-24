from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "OK"}

@app.get("/pay")
def pay():
    return {
        "btc_address": "bc1qtest123",
        "api_key": "sk_test_123",
        "amount_btc": 0.0001
    }

@app.get("/app", response_class=HTMLResponse)
def app_page():
    return """
    <html>
    <body style="background:black;color:white;text-align:center;">
        <h1>Bitcoin API</h1>
        <button onclick="pay()">Unlock</button>
        <p id="result"></p>

        <script>
        async function pay(){
            let r = await fetch('/pay');
            let d = await r.json();
            document.getElementById('result').innerHTML =
                "Key: " + d.api_key + "<br>BTC: " + d.amount_btc;
        }
        </script>
    </body>
    </html>
    """