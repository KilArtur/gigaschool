from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from database.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self) -> List[T]:
        return self.session.query(self.model).all()

    def update(self, instance: T) -> T:
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, instance: T) -> None:
        self.session.delete(instance)
        self.session.commit()

    def delete_by_id(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if instance:
            self.delete(instance)
            return True
        return False