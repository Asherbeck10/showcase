from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    ref = Column(Integer, primary_key=True, index=True)
    isin = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    bank = Column(String, nullable=False)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    market_end_time = Column(String, nullable=True)
