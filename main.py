import hashlib
from datetime import datetime
from core import verify_signature
from certificate import generate_certificate


if __name__ == "__main__":

    print("=" * 40)
    print(" BITCOIN PROOF ENGINE v2")
    print("=" * 40)

    address = input("\nAdresse Bitcoin: ")
    message = input("Message: ")
    signature = input("Signature: ")

    print("\nVérification en cours...\n")

    if address.startswith("1"):
        address_type = "Legacy (P2PKH)"
    elif address.startswith("bc1"):
        address_type = "SegWit (Bech32)"
    else:
        address_type = "Non supporté"

    result = verify_signature(address, signature, message)

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message_hash = hashlib.sha256(message.encode()).hexdigest()

    print("=" * 40)
    print("Adresse :", address)
    print("Type :", address_type)
    print("Horodatage :", timestamp)
    print("Hash message :", message_hash)

    if result:
        print("\nStatut : ✅ VALID SIGNATURE")
        filename = generate_certificate(
            address,
            address_type,
            message,
            signature,
            "VALID"
        )
        print("📄 Certificat généré :", filename)
    else:
        print("\nStatut : ❌ INVALID SIGNATURE")

    print("=" * 40)