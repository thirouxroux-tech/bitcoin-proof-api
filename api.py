import os
from flask import Flask, request, jsonify
from core import verify_signature
from certificate import generate_certificate
from datetime import datetime
import hashlib
import uuid

app = Flask(__name__)

# 🔐 API KEY via variable d’environnement
API_KEY = os.environ.get("API_KEY")


# 🌍 Route accueil
@app.route("/")
def home():
    return jsonify({
        "service": "Bitcoin Proof Engine API",
        "status": "online",
        "version": "2.0",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    })


# 🔎 Route vérification
@app.route("/verify", methods=["POST"])
def verify():

    # 🔐 Vérification clé API
    client_key = request.headers.get("X-API-KEY")
    if not API_KEY or client_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    address = data.get("address")
    message = data.get("message")
    signature = data.get("signature")

    if not address or not message or not signature:
        return jsonify({"error": "Missing parameters"}), 400

    # 🔍 Vérification signature
    is_valid, address_type = verify_signature(address, message, signature)

    if not is_valid:
        return jsonify({"status": "invalid"}), 400

    # 🧮 Hash message
    message_hash = hashlib.sha256(message.encode()).hexdigest()

    # 🆔 ID unique
    verification_id = str(uuid.uuid4())[:8]

    # 📄 Génération certificat PDF
    certificate_file = generate_certificate(
        address,
        message,
        signature,
        message_hash,
        address_type,
        verification_id
    )

    return jsonify({
        "status": "valid",
        "type": address_type,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "message_hash": message_hash,
        "verification_id": verification_id,
        "certificate_file": certificate_file
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)