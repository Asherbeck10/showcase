from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product
from app.auth import get_current_user

router = APIRouter()


@router.get("/products")
async def list_products(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return [
        {
            "ref": p.ref,
            "isin": p.isin,
            "description": p.description,
            "bank": p.bank,
            "bid": p.bid,
            "ask": p.ask,
        }
        for p in products
    ]
