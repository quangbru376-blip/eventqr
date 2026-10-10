import secrets

from hmac_utils import sign_ticket, verify_ticket

# Khóa thử chỉ tồn tại trong bộ nhớ, không in ra màn hình.
key = secrets.token_bytes(32)

payload = sign_ticket(
    "TEST-WEEK1", "TEST-TICKET-001", key
)

cases = [
    ("Ve hop le", payload, key, True),
    (
        "Sua eventId",
        payload.replace("TEST-WEEK1", "TEST-WEEK2", 1),
        key,
        False
    ),
    (
        "Sua ticketId",
        payload.replace("TEST-TICKET-001", "TEST-TICKET-002", 1),
        key,
        False
    ),
    (
        "Sua chu ky",
        payload[:-1] + ("A" if payload[-1] != "A" else "B"),
        key,
        False
    ),
    ("Sai khoa", payload, secrets.token_bytes(32), False),
    ("Sai dinh dang", "QR-GIA", key, False),
    ("Sai version", payload.replace("v1.", "v2.", 1), key, False),
]

for name, value, test_key, expected in cases:
    actual = verify_ticket(value, test_key)
    assert actual == expected, f"FAIL: {name}"
    print(f"PASS: {name}")

print("Tat ca 7 bai thu HMAC thanh cong.")