from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_ref = Column(String, unique=True, nullable=False, index=True)
    product_ref = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    buy_sell = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    notional = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
