from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
    <title>BitcoinProof</title>
    </head>

    <body style="font-family:Arial;text-align:center;padding:40px">

    <h1>BitcoinProof API</h1>

    <p>Server running</p>

    <p>
    <a href="/dashboard">Dashboard</a>
    </p>

    </body>
    </html>
    """

@app.get("/dashboard")
def dashboard():

    file="dashboard.html"

    if os.path.exists(file):
        return FileResponse(file)

    return {"error":"dashboard.html not found"}



