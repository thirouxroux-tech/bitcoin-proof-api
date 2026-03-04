import hashlib
import base64
import base58
import uuid
from datetime import datetime
from coincurve import PublicKey

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


# -------------------------------------------------
# Bitcoin message hash
# -------------------------------------------------
def bitcoin_message_hash(message: str) -> bytes:
    prefix = b"\x18Bitcoin Signed Message:\n"
    message_bytes = message.encode("utf-8")
    length = len(message_bytes)

    def encode_varint(i):
        if i < 253:
            return bytes([i])
        raise ValueError("Message too long")

    payload = prefix + encode_varint(length) + message_bytes
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()


# -------------------------------------------------
# Vérification Legacy (P2PKH)
# -------------------------------------------------
def verify_legacy(address: str, signature: str, message: str):
    try:
        if not signature.strip():
            print("Signature vide")
            return False

        sig = base64.b64decode(signature)

        header = sig[0]
        if header < 27 or header > 35:
            print("Header signature invalide")
            return False

        recovery_id = (header - 27) & 3
        compressed = ((header - 27) & 4) != 0

        signature_bytes = sig[1:]
        compact_sig = signature_bytes + bytes([recovery_id])

        msg_hash = bitcoin_message_hash(message)

        pubkey = PublicKey.from_signature_and_message(
            compact_sig,
            msg_hash,
            hasher=None
        )

        pubkey_bytes = pubkey.format(compressed=compressed)

        sha = hashlib.sha256(pubkey_bytes).digest()
        rip = hashlib.new("ripemd160", sha).digest()

        versioned = b"\x00" + rip
        checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]

        generated_address = base58.b58encode(versioned + checksum).decode()

        return generated_address == address

    except Exception as e:
        print("Erreur:", e)
        return False


# -------------------------------------------------
# Génération certificat PDF
# -------------------------------------------------
def generate_certificate(address, address_type, message, signature, status):

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    certificate_id = str(uuid.uuid4())[:8]
    filename = f"certificate_{certificate_id}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    elements.append(Paragraph("<b>BITCOIN PROOF CERTIFICATE</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"<b>Certificate ID:</b> {certificate_id}", normal))
    elements.append(Paragraph(f"<b>Adresse:</b> {address}", normal))
    elements.append(Paragraph(f"<b>Type:</b> {address_type}", normal))
    elements.append(Paragraph(f"<b>Message:</b> {message}", normal))
    elements.append(Paragraph(f"<b>Signature:</b> {signature}", normal))
    elements.append(Paragraph(f"<b>Status:</b> {status}", normal))
    elements.append(Paragraph(f"<b>Horodatage:</b> {timestamp}", normal))

    message_hash = hashlib.sha256(message.encode()).hexdigest()
    elements.append(Paragraph(f"<b>Message Hash:</b> {message_hash}", normal))

    certificate_hash = hashlib.sha256(
        (address + message + signature + timestamp).encode()
    ).hexdigest()

    elements.append(Paragraph(f"<b>Certificate Internal Hash:</b> {certificate_hash}", normal))

    doc.build(elements)

    print(f"\n📄 Certificat généré : {filename}")


# -------------------------------------------------
# Programme principal
# -------------------------------------------------
if __name__ == "__main__":

    print("=" * 40)
    print(" BITCOIN PROOF ENGINE v1")
    print("=" * 40)

    address = input("\nAdresse Bitcoin: ")
    message = input("Message: ")
    signature = input("Signature: ")

    print("\nVérification en cours...\n")

    if address.startswith("1"):
        result = verify_legacy(address, signature, message)
        address_type = "Legacy (P2PKH)"
    else:
        result = False
        address_type = "Non supporté"

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message_hash = hashlib.sha256(message.encode()).hexdigest()

    print("=" * 40)
    print("Adresse :", address)
    print("Type :", address_type)
    print("Horodatage :", timestamp)
    print("Hash message :", message_hash)

    if result:
        print("\nStatut : ✅ VALID SIGNATURE")
        generate_certificate(address, address_type, message, signature, "VALID")
    else:
        print("\nStatut : ❌ INVALID SIGNATURE")

    print("=" * 40)