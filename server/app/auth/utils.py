import secrets
import hashlib

def generate_auth_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def hash_auth_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_auth_token(
    token: str,
    token_hash: str,
) -> bool:
    return secrets.compare_digest(
        hash_auth_token(token),
        token_hash,
    )
if __name__ == "__main__":
    token = generate_auth_token()
    print(token)