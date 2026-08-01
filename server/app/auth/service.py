from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

from .exceptions import InvalidToken


class AuthService:

    async def authenticate(self, token: str) -> User:
        async with SessionLocal() as session:

            result = await session.execute(
                select(User).where(User.token == token)
            )

            user = result.scalar_one_or_none()

            if user is None:
                raise InvalidToken()

            return user


auth_service = AuthService()