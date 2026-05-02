from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():

    return """
    <!DOCTYPE html>
    <html>

    <head>
        <title>LightningDrop</title>

        <style>

        body{
            background:#0f0f0f;
            color:white;
            font-family:Arial;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            margin:0;
        }

        .card{
            background:#171717;
            padding:40px;
            border-radius:20px;
            width:400px;
            text-align:center;
        }

        h1{
            font-size:40px;
        }

        p{
            color:#999;
            margin-bottom:30px;
        }

        button{
            background:#f7931a;
            color:black;
            border:none;
            padding:16px 24px;
            border-radius:12px;
            font-size:18px;
            cursor:pointer;
            font-weight:bold;
        }

        </style>

    </head>

    <body>

        <div class="card">

            <h1>⚡ LightningDrop</h1>

            <p>
            Sell digital files with Bitcoin.
            </p>

            <button>
            Create Paywall
            </button>

        </div>

    </body>

    </html>
    """