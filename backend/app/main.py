import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.database import engine, Base
from app.models import user, product, trade  # noqa: F401 — ensure models are registered
from app.seed import seed
from app.routers import auth, products, rfq, trades


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    yield


app = FastAPI(title="Trading Demo", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(rfq.router)
app.include_router(trades.router)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/",
    StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True),
    name="static"
)