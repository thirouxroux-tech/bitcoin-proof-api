from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    return {"status": "OK"}

@app.get("/app", response_class=HTMLResponse)
def app_page():
    return """
    <html>
    <body style="background:black;color:white;text-align:center;">
        <h1>🚀 APP OK</h1>
        <button onclick="alert('WORKING')">TEST</button>
    </body>
    </html>
    """