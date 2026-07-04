import secrets

def generate_stream_key() -> str:
    return secrets.token_urlsafe(32)