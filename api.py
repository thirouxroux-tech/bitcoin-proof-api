from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "OK"}

@app.get("/pay")
def pay():
    amount_btc = 0.0001

    return {
        "btc_address": "bc1qxxxxxxxxxxxxxxxxxxxxx",  # TON adresse
        "amount_btc": amount_btc,
        "currency": "BTC"
    }    }

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
        "Adresse BTC:<br>" + d.btc_address +
        "<br><br>Montant: " + d.amount_btc + " BTC";
}
</script>
    </body>
    </html>
    """