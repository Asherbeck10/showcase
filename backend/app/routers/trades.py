from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.trade import Trade
from app.models.user import User
from app.auth import get_current_user

router = APIRouter()


class TradeRequest(BaseModel):
    product_ref: int
    buy_sell: str
    quantity: float
    price: float


def _trade_dict(t: Trade) -> dict:
    return {
        "id": t.id,
        "trade_ref": t.trade_ref,
        "product_ref": t.product_ref,
        "buy_sell": t.buy_sell,
        "quantity": t.quantity,
        "price": t.price,
        "notional": t.notional,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/orders")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    result = await db.execute(select(Trade).where(Trade.user_id == user.id).order_by(Trade.id.desc()))
    return [_trade_dict(t) for t in result.scalars().all()]


@router.get("/orders/pending")
async def list_pending_orders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("usertype") != "bank":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bank access only")

    result = await db.execute(
        select(Trade).where(Trade.status == "PENDING").order_by(Trade.id.asc())
    )
    return [_trade_dict(t) for t in result.scalars().all()]


@router.get("/orders/approved")
async def list_approved_orders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("usertype") != "bank":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bank access only")

    result = await db.execute(
        select(Trade).where(Trade.status == "CONFIRMED").order_by(Trade.id.desc())
    )
    return [_trade_dict(t) for t in result.scalars().all()]


@router.post("/orders/{trade_ref}/approve")
async def approve_order(
    trade_ref: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("usertype") != "bank":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bank access only")

    result = await db.execute(select(Trade).where(Trade.trade_ref == trade_ref))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    if trade.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Trade is already {trade.status}")

    trade.status = "CONFIRMED"
    await db.commit()
    await db.refresh(trade)
    return {"trade_ref": trade.trade_ref, "status": trade.status}


@router.post("/trade", status_code=status.HTTP_201_CREATED)
async def place_trade(
    body: TradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if body.buy_sell.upper() not in ("BUY", "SELL"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="buy_sell must be BUY or SELL")
    if body.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quantity must be positive")

    result = await db.execute(select(User).where(User.username == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Generate trade ref
    result = await db.execute(select(Trade))
    count = len(result.scalars().all())
    trade_ref = f"TRD-{count + 1:04d}"

    # Ensure unique ref
    while True:
        check = await db.execute(select(Trade).where(Trade.trade_ref == trade_ref))
        if not check.scalar_one_or_none():
            break
        count += 1
        trade_ref = f"TRD-{count + 1:04d}"

    notional = body.quantity * body.price
    trade = Trade(
        trade_ref=trade_ref,
        product_ref=body.product_ref,
        user_id=user.id,
        buy_sell=body.buy_sell.upper(),
        quantity=body.quantity,
        price=body.price,
        notional=notional,
        status="PENDING",
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)

    return {"trade_ref": trade.trade_ref, "status": trade.status, "notional": trade.notional}
