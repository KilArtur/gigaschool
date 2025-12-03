from typing import Optional
from sqlalchemy.orm import Session
from database.models.wallet_model import WalletModel
from database.repositories.base_repository import BaseRepository
from datetime import datetime


class WalletRepository(BaseRepository[WalletModel]):
    def __init__(self, session: Session):
        super().__init__(session, WalletModel)

    def get_by_user_id(self, user_id: int) -> Optional[WalletModel]:
        return self.session.query(WalletModel).filter(WalletModel.user_id == user_id).first()

    def add_balance(self, wallet_id: int, amount: float) -> Optional[WalletModel]:
        wallet = self.get_by_id(wallet_id)
        if wallet:
            wallet.balance += amount
            wallet.updated_at = datetime.now()
            return self.update(wallet)
        return None

    def deduct_balance(self, wallet_id: int, amount: float) -> Optional[WalletModel]:
        wallet = self.get_by_id(wallet_id)
        if wallet and wallet.balance >= amount:
            wallet.balance -= amount
            wallet.updated_at = datetime.now()
            return self.update(wallet)
        return None

    def set_balance(self, wallet_id: int, new_balance: float) -> Optional[WalletModel]:
        wallet = self.get_by_id(wallet_id)
        if wallet:
            wallet.balance = new_balance
            wallet.updated_at = datetime.now()
            return self.update(wallet)
        return None