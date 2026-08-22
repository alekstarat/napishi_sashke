from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey,
    X25519PrivateKey
)
from cryptography.hazmat.primitives.ciphers.aead import  AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.exceptions import InvalidTag
import base64
from pathlib import Path
import os

class CryptoService:
    def __init__(self) -> None:
        keys_dir = Path(__file__).parent.parent / "keys"

        private_path = keys_dir / "private.key"
        public_path = keys_dir / "public.key"

        if not private_path.exists():
            raise FileNotFoundError(f"Private key not found: {private_path}")

        if not public_path.exists():
            raise FileNotFoundError(f"Public key not found: {public_path}")

        private_bytes = base64.b64decode(
            private_path.read_text(encoding="utf-8")
        )

        public_bytes = base64.b64decode(public_path.read_text(encoding="utf-8"))

        self._private_key = X25519PrivateKey.from_private_bytes(
            private_bytes
        )

        self._public_key = X25519PublicKey.from_public_bytes(
            public_bytes
        )

    @property
    def public_key(self) -> bytes:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def export_public_key(self) -> str:
        return base64.b64encode(
            self.public_key
        ).decode("utf-8")

    @staticmethod
    def import_public_key(
            public_key: str
    ) -> X25519PublicKey:
        return X25519PublicKey.from_public_bytes(base64.b64decode(public_key))

    def shared_secret(
            self,
            peer_public_key: X25519PublicKey
    ) -> bytes:
        return self._private_key.exchange(peer_public_key)

    def derive_key(
            self,
            peer_public_key: X25519PublicKey
    ) -> bytes:
        secret = self.shared_secret(peer_public_key)

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"private-messenger"
        )

        return hkdf.derive(secret)

    def encrypt_bytes(
            self,
            data: bytes,
            peer_public_key: X25519PublicKey
    ) -> bytes:
        key = self.derive_key(peer_public_key)

        aes = AESGCM(key)

        nonce = os.urandom(12)

        encrypted = aes.encrypt(
            nonce,
            data,
            None
        )

        return nonce + encrypted

    def decrypt_bytes(
            self,
            data: bytes,
            peer_public_key: X25519PublicKey,
    ) -> bytes:
        key = self.derive_key(peer_public_key)

        nonce = data[:12]
        encrypted = data[12:]

        aes = AESGCM(key)

        return aes.decrypt(
            nonce,
            encrypted,
            None,
        )

    def encrypt(
            self,
            plaintext: str,
            peer_public_key: X25519PublicKey,
    ) -> str:
        encrypted = self.encrypt_bytes(
            plaintext.encode("utf-8"),
            peer_public_key,
        )

        return base64.b64encode(
            encrypted
        ).decode("utf-8")

    def decrypt(
            self,
            ciphertext: str,
            peer_public_key: X25519PublicKey,
    ) -> str:
        encrypted = base64.b64decode(ciphertext)

        plaintext = self.decrypt_bytes(
            encrypted,
            peer_public_key,
        )

        return plaintext.decode("utf-8")

    def try_decrypt(
            self,
            text: str,
            peer_public_key: X25519PublicKey
    ) -> str:
        try:
            return self.decrypt(ciphertext=text, peer_public_key=peer_public_key)
        except (InvalidTag, ValueError):
            return text