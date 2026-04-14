from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import hashlib
import uuid
import json
import os

app = FastAPI()

FILE = "proofs.json"

# ======================
# LOAD / SAVE
# ======================

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

# ======================
# HOME
# ======================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>Bitcoin Proof</h1>
    <a href="/verify-page">Create Proof</a>
    <br><br>
    <a href="/dashboard">Dashboard</a>
    <br><br>
    <a href="/explorer">Explorer</a>
    """

# ======================
# VERIFY PAGE
# ======================

@app.get("/verify-page", response_class=HTMLResponse)
def verify_page():
    return """
    <h1>Create Proof</h1>

    <input id="msg" placeholder="Enter text">
    <button onclick="send()">Create</button>

    <div id="result"></div>

    <script>
    async function send(){

        let msg = document.getElementById("msg").value

        let res = await fetch("/verify",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body: JSON.stringify({message: msg})
        })

        let data = await res.json()

        if(data.error){
            document.getElementById("result").innerText = data.error
            return
        }

        let url = "/proof/" + data.id

        document.getElementById("result").innerHTML =
        "<p>Proof created</p><a href='" + url + "'>View proof</a>"
    }
    </script>
    """

# ======================
# CREATE PROOF
# ======================

@app.post("/verify")
def verify(data: dict):

    msg = data.get("message", "")

    if msg == "":
        return {"error": "empty message"}

    h = hashlib.sha256(msg.encode()).hexdigest()
    pid = str(uuid.uuid4())[:8]

    proofs = load()

    proofs[pid] = {
        "id": pid,
        "message": msg,
        "hash": h
    }

    save(proofs)

    return {"id": pid}

# ======================
# PROOF PAGE
# ======================

@app.get("/proof/{pid}", response_class=HTMLResponse)
def proof(pid: str):

    proofs = load()

    if pid not in proofs:
        return HTMLResponse("<h1>Proof not found</h1>", status_code=404)

    p = proofs[pid]

    return f"""
    <h1>Proof</h1>

    <p><b>ID:</b> {p['id']}</p>
    <p><b>Message:</b> {p['message']}</p>
    <p><b>Hash:</b> {p['hash']}</p>

    <br>
    <a href="/dashboard">Dashboard</a>
    """

# ======================
# DASHBOARD
# ======================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    proofs = load()

    html = "<h1>Dashboard</h1>"

    if len(proofs) == 0:
        html += "<p>No proofs yet</p>"

    for p in proofs.values():
        html += f"""
        <div style="margin:10px;padding:10px;border:1px solid white;">
            <p><b>ID:</b> {p['id']}</p>
            <p><b>Message:</b> {p['message']}</p>
            <p><b>Hash:</b> {p['hash']}</p>
            <a href="/proof/{p['id']}">View proof</a>
        </div>
        """

    html += "<br><a href='/'>Home</a>"

    return html

# ======================
# EXPLORER
# ======================

@app.get("/explorer", response_class=HTMLResponse)
def explorer():

    proofs = load()

    html = "<h1>All Proofs</h1>"

    for p in proofs.values():
        html += f"""
        <div>
            <a href="/proof/{p['id']}">{p['id']}</a>
            - {p['hash']}
        </div>
        """

    html += "<br><a href='/'>Home</a>"

    return html