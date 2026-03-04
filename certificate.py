import hashlib
import uuid
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


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

    return filename