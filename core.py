import hashlib
import base64
import base58
from coincurve import PublicKey
from bech32 import bech32_encode, convertbits


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


def pubkey_to_p2pkh(pubkey_bytes: bytes) -> str:
    sha = hashlib.sha256(pubkey_bytes).digest()
    rip = hashlib.new("ripemd160", sha).digest()
    versioned = b"\x00" + rip
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return base58.b58encode(versioned + checksum).decode()


def pubkey_to_bech32(pubkey_bytes: bytes) -> str:
    sha = hashlib.sha256(pubkey_bytes).digest()
    rip = hashlib.new("ripemd160", sha).digest()

    # witness version 0
    converted = convertbits(rip, 8, 5)
    return bech32_encode("bc", [0] + converted)


def verify_signature(address: str, signature: str, message: str):

    try:
        if not signature.strip():
            return False

        sig = base64.b64decode(signature)

        header = sig[0]
        if header < 27 or header > 35:
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

        # Cas Legacy
        if address.startswith("1"):
            generated = pubkey_to_p2pkh(pubkey_bytes)
            return generated == address

        # Cas Bech32 bc1
        if address.startswith("bc1"):
            generated = pubkey_to_bech32(pubkey_bytes)
            return generated == address

        return False

    except Exception:
        return False