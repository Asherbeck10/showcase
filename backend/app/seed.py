import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.trade import Trade


USERS = [
    {"username": "demo_client", "password": "demo123", "usertype": "client"},
    {"username": "demo_bank",   "password": "demo123", "usertype": "bank"},
]

PRODUCTS = [
    {"isin": "XS1111111111", "description": "JPMorgan FTSE 100 Autocall", "bank": "JPMorgan", "bid": 98.50, "ask": 101.25},
    {"isin": "XS2222222222", "description": "Goldman MSCI World Note",    "bank": "Goldman",  "bid": 97.00, "ask": 100.50},
    {"isin": "XS3333333333", "description": "Barclays S&P 500 Tracker",   "bank": "Barclays", "bid": 99.10, "ask": 102.00},
    {"isin": "XS4444444444", "description": "HSBC Euro Note",             "bank": "HSBC",     "bid": 96.50, "ask": 99.75},
    {"isin": "XS5555555555", "description": "UBS Tech Autocall",          "bank": "UBS",      "bid": 98.00, "ask": 101.00},
]

PRE_SEEDED_TRADES = [
    {"trade_ref": "TRD-0001", "product_ref": 1, "buy_sell": "BUY",  "quantity": 100000, "price": 101.25, "status": "CONFIRMED"},
    {"trade_ref": "TRD-0002", "product_ref": 2, "buy_sell": "BUY",  "quantity":  50000, "price": 100.50, "status": "CONFIRMED"},
    {"trade_ref": "TRD-0003", "product_ref": 3, "buy_sell": "SELL", "quantity":  75000, "price":  99.10, "status": "PENDING"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        # Seed users
        user_ids = {}
        for u in USERS:
            result = await db.execute(select(User).where(User.username == u["username"]))
            if result.scalar_one_or_none() is None:
                user = User(
                    username=u["username"],
                    password=bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode(),
                    usertype=u["usertype"],
                )
                db.add(user)
                await db.flush()
                user_ids[u["username"]] = user.id

        # Seed products
        for p in PRODUCTS:
            result = await db.execute(select(Product).where(Product.isin == p["isin"]))
            if result.scalar_one_or_none() is None:
                db.add(Product(**p))

        await db.flush()

        # Resolve demo_client user id
        result = await db.execute(select(User).where(User.username == "demo_client"))
        demo_user = result.scalar_one()

        # Seed trades
        for t in PRE_SEEDED_TRADES:
            result = await db.execute(select(Trade).where(Trade.trade_ref == t["trade_ref"]))
            if result.scalar_one_or_none() is None:
                notional = t["quantity"] * t["price"]
                db.add(Trade(
                    trade_ref=t["trade_ref"],
                    product_ref=t["product_ref"],
                    user_id=demo_user.id,
                    buy_sell=t["buy_sell"],
                    quantity=t["quantity"],
                    price=t["price"],
                    notional=notional,
                    status=t["status"],
                ))

        await db.commit()
