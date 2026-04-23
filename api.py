from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "OK ROOT"}

@app.get("/app", response_class=HTMLResponse)
def app_page():
    return "<h1>APP OK</h1>"