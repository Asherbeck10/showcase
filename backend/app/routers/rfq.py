from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product
from app.auth import get_current_user

router = APIRouter()


@router.get("/rfq/{product_ref}")
async def get_rfq(
    product_ref: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.ref == product_ref))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return {
        "product_ref": product.ref,
        "isin": product.isin,
        "description": product.description,
        "price": product.ask,
        "valid_for_seconds": 30,
    }
