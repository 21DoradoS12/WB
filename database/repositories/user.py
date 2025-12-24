from typing import Optional

from src.database.models import UserORM
from src.database.repositories import BaseRepository
from src.domain.models.user import User


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> Optional[User]:
        user = await self.session.get(UserORM, user_id)

        if not user:
            return None

        return User.model_validate(user)
