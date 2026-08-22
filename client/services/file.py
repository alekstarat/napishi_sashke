from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey
)
from services.crypto import CryptoService
import httpx

class FileService:
    def __init__(
            self,
            crypto: CryptoService,
            server_url: str
    ) -> None:
        self.crypto = crypto
        self.server_url = server_url.rstrip("/")

    def encrypt_file(
            self,
            source: Path,
            destination: Path,
            peer_public_key: X25519PublicKey
    ) -> None:
        data = source.read_bytes()

        encrypted = self.crypto.encrypt_bytes(
            data, peer_public_key
        )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encrypted)

    def decrypt_file(
            self,
            source: Path,
            destination: Path,
            peer_public_key: X25519PublicKey
    ) -> None:
        encrypted = source.read_bytes()

        decrypted = self.crypto.decrypt_bytes(
            encrypted,
            peer_public_key,
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(
            decrypted
        )

    async def upload_file(
            self,
            path: Path,
            peer_public_key: X25519PublicKey
    ) -> str:
        data = path.read_bytes()

        encrypted = self.crypto.encrypt_bytes(
            data, peer_public_key
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/files/",
                content=encrypted
            )

        response.raise_for_status()

        return response.json()["file_id"]

    async def download_file(
            self,
            file_id: str,
            destination: Path,
            peer_public_key: X25519PublicKey,
    ) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/files/{file_id}"
            )

        response.raise_for_status()

        decrypted = self.crypto.decrypt_bytes(
            response.content,
            peer_public_key,
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(
            decrypted,
        )
