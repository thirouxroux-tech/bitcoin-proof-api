from flask import Flask, request, jsonify
from datetime import datetime
import hashlib
import uuid

from core import verify_signature
from certificate import generate_certificate

app = Flask(__name__)

# 🔐 Liste des clés API autorisées
VALID_API_KEYS = {
    "dev_key_123456",   # clé de test
}


def require_api_key(req):
    api_key = req.headers.get("X-API-KEY")
    if not api_key:
        return False
    return api_key in VALID_API_KEYS


@app.route("/verify", methods=["POST"])
def verify():

    # 🔒 Vérification clé API
    if not require_api_key(request):
        return jsonify({"error": "Unauthorized - Invalid or missing API key"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    address = data.get("address")
    message = data.get("message")
    signature = data.get("signature")

    if not address or not message or not signature:
        return jsonify({"error": "address, message and signature required"}), 400

    # Type adresse
    if address.startswith("1"):
        address_type = "Legacy (P2PKH)"
    elif address.startswith("bc1"):
        address_type = "SegWit (Bech32)"
    else:
        address_type = "Unsupported"

    result = verify_signature(address, signature, message)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_hash = hashlib.sha256(message.encode()).hexdigest()
    verification_id = str(uuid.uuid4())[:8]

    if result:
        certificate_file = generate_certificate(
            address,
            address_type,
            message,
            signature,
            "VALID"
        )
        status = "valid"
    else:
        certificate_file = None
        status = "invalid"

    return jsonify({
        "verification_id": verification_id,
        "status": status,
        "type": address_type,
        "timestamp": timestamp,
        "message_hash": message_hash,
        "certificate_file": certificate_file
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)