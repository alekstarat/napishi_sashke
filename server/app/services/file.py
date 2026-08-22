from pathlib import Path
from uuid import uuid4


class FileService:
    def __init__(self) -> None:
        self.storage = (
            Path(__file__).parent.parent.parent
            / "storage"
            / "files"
        )

        self.storage.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        data: bytes,
    ) -> str:
        file_id = uuid4().hex

        path = self.storage / file_id

        path.write_bytes(data)

        return file_id

    def load(
        self,
        file_id: str,
    ) -> bytes:
        path = self.storage / file_id

        if not path.exists():
            raise FileNotFoundError(file_id)

        return path.read_bytes()