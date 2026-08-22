import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from tools.generate_token import generate_auth_token

KEYS_DIR = Path(__file__).parent.parent / "keys"


def save_key(path: Path, data: bytes) -> None:
    path.write_text(
        base64.b64encode(data).decode("utf-8"),
        encoding="utf-8",
    )


def main(usernames: list[str]) -> None:
    KEYS_DIR.mkdir(exist_ok=True)

    for name in usernames:

        private_key = X25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        os.mkdir(KEYS_DIR / name)

        save_key(KEYS_DIR / name / "private.key", private_bytes)
        save_key(KEYS_DIR / name / "public.key", public_bytes)

        print(f"\n{name} - {generate_auth_token()}")


if __name__ == "__main__":
    #main(["сашер", "соткин", "лёшк", "киорио"])
    main(["соткин"])