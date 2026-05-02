from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        width:420px;
        text-align:center;
    }

    h1{
        font-size:40px;
    }

    p{
        color:#999;
        margin-bottom:30px;
    }

    input{
        width:100%;
        padding:14px;
        margin-bottom:20px;
        border-radius:10px;
        border:none;
        background:#222;
        color:white;
    }

    button{
        background:#f7931a;
        color:black;
        border:none;
        padding:16px;
        width:100%;
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
            Sell digital files with Bitcoin
            </p>

            <form
            action="/create"
            method="post"
            enctype="multipart/form-data"
            >

                <input
                type="file"
                name="file"
                required
                >

                <input
                type="text"
                name="price"
                placeholder="Price in BTC"
                required
                >

                <button type="submit">
                Create Paywall
                </button>

            </form>

        </div>

    </body>

    </html>
    """

@app.post("/create")
async def create(
    price: str = Form(...),
    file: UploadFile = File(...)
):

    filepath = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return HTMLResponse(f"""

    <html>

    <body style="
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:100px;
    ">

        <h1>✅ File Uploaded</h1>

        <p>
        Price: {price} BTC
        </p>

        <p>
        File: {file.filename}
        </p>

    </body>

    </html>

    """)