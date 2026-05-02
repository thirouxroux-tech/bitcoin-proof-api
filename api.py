from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import os
import uuid

app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

FILES_DB = {}

# ==================================================
# HOME
# ==================================================

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

# ==================================================
# CREATE PAYWALL
# ==================================================

@app.post("/create")
async def create(
    price: str = Form(...),
    file: UploadFile = File(...)
):

    file_id = str(uuid.uuid4())[:8]

    filename = f"{file_id}_{file.filename}"

    filepath = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(filepath, "wb") as f:
        f.write(await file.read())

    FILES_DB[file_id] = {
        "filename": filename,
        "price": price
    }

    return HTMLResponse(f"""

    <html>

    <body style="
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:100px;
    ">

        <h1>✅ Paywall Created</h1>

        <p>
        Share this link:
        </p>

        <a
        href="/pay/{file_id}"
        style="
            color:#f7931a;
            font-size:22px;
        "
        >
        /pay/{file_id}
        </a>

    </body>

    </html>

    """)

# ==================================================
# PAY PAGE
# ==================================================

@app.get("/pay/{file_id}", response_class=HTMLResponse)
def pay(file_id: str):

    if file_id not in FILES_DB:
        return HTMLResponse("Not found")

    data = FILES_DB[file_id]

    return HTMLResponse(f"""

    <html>

    <body style="
        background:#0f0f0f;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:100px;
    ">

        <h1>🔒 Locked File</h1>

        <p>
        Price:
        </p>

        <h2>{data["price"]} BTC</h2>

        <button style="
            background:#f7931a;
            color:black;
            border:none;
            padding:16px 24px;
            border-radius:12px;
            font-size:18px;
            font-weight:bold;
        ">
        Bitcoin Payment Coming Soon
        </button>

    </body>

    </html>

    """)