from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship, declarative_base, Session
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError


Base = declarative_base()


class DbBaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())

    @classmethod
    def get_one(cls, db_session: Session, **kwargs):
        try:
            return db_session.query(cls).filter_by(**kwargs).one_or_none()
        except SQLAlchemyError as e:
            db_session.rollback()
            raise e


class StoreModel(DbBaseModel):
    __tablename__ = 'store'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    search_name = Column(String, nullable=False)
    review = relationship("ReviewModel", uselist=False, back_populates="store")


class ReviewModel(DbBaseModel):
    __tablename__ = 'review'
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String, nullable=False)
    comment = Column(String)
    rating = Column(Numeric(13, 2), nullable=False)
    rating_scale = Column(Numeric(13, 2), nullable=False)
    store_id = Column(Integer, ForeignKey("store.id"))
    store = relationship("StoreModel", back_populates="review")
    estimated_date = Column(DateTime(timezone=True), nullable=False)
