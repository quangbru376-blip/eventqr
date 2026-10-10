import base64
import hashlib
import hmac


def sign_ticket(event_id, ticket_id, key):
    if not event_id or not ticket_id:
        raise ValueError("eventId và ticketId không được rỗng")

    if "." in event_id or "." in ticket_id:
        raise ValueError("ID không được chứa dấu chấm")

    message = f"v1.{event_id}.{ticket_id}"
    digest = hmac.new(
        key,
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    signature = base64.urlsafe_b64encode(
        digest
    ).decode("ascii").rstrip("=")

    return f"{message}.{signature}"


def verify_ticket(payload, key):
    if not isinstance(payload, str):
        return False

    parts = payload.split(".")
    if len(parts) != 4:
        return False

    version, event_id, ticket_id, signature = parts
    if version != "v1" or not event_id or not ticket_id:
        return False

    # HMAC-SHA256 dạng base64url bỏ padding dài 43 ký tự.
    if len(signature) != 43:
        return False

    expected = sign_ticket(
        event_id, ticket_id, key
    ).split(".")[-1]

    return hmac.compare_digest(
        expected.encode("ascii"),
        signature.encode("utf-8")
    )