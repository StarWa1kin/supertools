import base64


def b64url_encode(value: bytes) -> str:
    """URL-safe base64 without padding, as used in signed tokens."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
