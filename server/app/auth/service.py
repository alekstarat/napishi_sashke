from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

from .exceptions import InvalidToken


class AuthService:

    async def authenticate(self, token: str, public_key: str) -> User:
        async with SessionLocal() as session:

            result = await session.execute(
                select(User).where(User.token == token)
            )

            user = result.scalar_one_or_none()

            if user is None:
                raise InvalidToken()

            return user

    async def get_public_key(
            self,
            username: str
    ) -> str:
        async with SessionLocal() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )

            user = result.scalar_one_or_none()

            if user is None:
                raise ValueError(f"Unknown user {username}")

            if user.public_key is None:
                raise ValueError(f"{username} has no public key")

            return user.public_key


auth_service = AuthService()