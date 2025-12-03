from typing import Optional, List
from sqlalchemy.orm import Session
from database.models.user_model import UserModel
from database.repositories.base_repository import BaseRepository
from core.models.user_role import UserRole


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, session: Session):
        super().__init__(session, UserModel)

    def get_by_username(self, username: str) -> Optional[UserModel]:
        return self.session.query(UserModel).filter(UserModel.username == username).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        return self.session.query(UserModel).filter(UserModel.email == email).first()

    def get_by_role(self, role: UserRole) -> List[UserModel]:
        return self.session.query(UserModel).filter(UserModel.role == role).all()

    def get_active_users(self) -> List[UserModel]:
        return self.session.query(UserModel).filter(UserModel.is_active == True).all()

    def update_balance(self, user_id: int, new_balance: float) -> Optional[UserModel]:
        user = self.get_by_id(user_id)
        if user:
            user.balance = new_balance
            return self.update(user)
        return None

    def deactivate_user(self, user_id: int) -> Optional[UserModel]:
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            return self.update(user)
        return None

    def activate_user(self, user_id: int) -> Optional[UserModel]:
        user = self.get_by_id(user_id)
        if user:
            user.is_active = True
            return self.update(user)
        return None