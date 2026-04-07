# Plan: Verto Trading Platform — Showcase Version (Sharp MVP)

## Goal

A clean, completable demo that shows the core trading flow:
**Login → Browse Products → Place a Trade → View Your Orders**

One simple HTML page served by FastAPI. SQLite in-memory. No GCP, no SendGrid, no frontend build toolchain.

---

## What's CUT (vs original plan)

| Removed                 | Why                                      |
| ----------------------- | ---------------------------------------- |
| Full Vite frontend      | Overkill — one plain HTML page is enough |
| /refresh endpoint       | Complexity without demo value            |
| /blotter endpoint       | Nice-to-have, not core flow              |
| Bank flows              | Separate concern, muddles the demo       |
| /bank/\* endpoints      | Out of scope                             |
| docker-compose          | One uvicorn command is simpler           |
| .npmrc / ci-postinstall | No npm at all — single static HTML file  |

---

## Database Setup (Critical Detail)

SQLite in-memory with async requires `StaticPool` to ensure all connections share the same in-memory database instance (otherwise each connection gets its own empty DB):

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

---

## Architecture

```text
verto-trading-demo/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app + mounts static HTML + runs seed on startup
│   │   ├── database.py    # SQLite in-memory, aiosqlite, SQLAlchemy async
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── trade.py
│   │   ├── seed.py        # Seeds demo data on startup
│   │   ├── auth.py        # JWT helpers (hardcoded demo secret, no Secret Manager)
│   │   └── routers/
│   │       ├── auth.py    # POST /token
│   │       ├── products.py# GET /products
│   │       ├── rfq.py     # GET /rfq/{product_ref}
│   │       └── trades.py  # GET /orders, POST /trade
│   ├── static/
│   │   └── index.html     # Single page: login + product list + trade form + orders
│   └── requirements.txt
└── README.md
```

---

## API Endpoints (7 total)

| Method | Path                          | Auth?      | Description                                                                                    |
| ------ | ----------------------------- | ---------- | ---------------------------------------------------------------------------------------------- |
| POST   | /token                        | No         | Login → returns JWT access token                                                               |
| GET    | /products                     | Yes        | List available products with bid/ask                                                           |
| GET    | /rfq/{product_ref}            | Yes        | Get live quote — returns product details + `price` (ask) + `valid_for_seconds: 30`             |
| GET    | /orders                       | Yes        | List caller's own trades                                                                       |
| POST   | /trade                        | Yes        | Place a trade — body: product_ref, buy_sell, quantity, price → notional calculated server-side |
| GET    | /orders/pending               | Bank only  | List all PENDING trades across all clients                                                     |
| GET    | /orders/approved              | Bank only  | List all CONFIRMED trades (past approvals)                                                     |
| POST   | /orders/{trade_ref}/approve   | Bank only  | Approve a PENDING trade → status becomes CONFIRMED                                             |

All protected endpoints use `Authorization: Bearer <token>` header.

---

## Trade Lifecycle

New trades are created with `status = "PENDING"`. This is visible in the My Orders table and shows the trade is awaiting confirmation.

The status column is displayed with a colour-coded badge:

- 🟡 **PENDING** — trade submitted, awaiting processing
- 🟢 **CONFIRMED** — trade confirmed (pre-seeded trades + future extension)

New trades placed via the UI always start as `PENDING`. The demo does not auto-confirm — this shows the lifecycle clearly and leaves room to extend.

---

## Frontend (single index.html)

One page, three sections shown/hidden by JS:

1. **Login form** — username + password → POST /token → stores token in memory
2. **Product list** — GET /products → table with "Trade" button per row
3. **Trade panel** — click Trade → GET /rfq/{ref} → form (buy/sell, amount) → POST /trade
4. **My Orders** — GET /orders → table showing placed trades with status badge (🟡 PENDING / 🟢 CONFIRMED)

Plain HTML + vanilla JS + minimal inline CSS. No build step, no npm.

**UX states handled:**

- **Loading** — spinner/disabled button while any API call is in flight
- **Error messages** — shown inline (e.g., "Invalid credentials", "Quote expired, please try again", "Trade failed")
- **Success message** — shown after trade submitted: "✅ Trade placed successfully — Ref: TRD-XXXX" with auto-dismiss after 3 seconds
- **Session expired** — 401 response shows "Session expired, please log in again" and returns to login section

---

## Demo Data (seeded on startup)

**Users:**

| Username    | Password | Type   |
| ----------- | -------- | ------ |
| demo_client | demo123  | client |
| demo_bank   | demo123  | bank   |

**Products (5):**

- JPMorgan FTSE 100 Autocall — XS1111111111 — Bid: 98.50, Ask: 101.25
- Goldman MSCI World Note — XS2222222222 — Bid: 97.00, Ask: 100.50
- Barclays S&P 500 Tracker — XS3333333333 — Bid: 99.10, Ask: 102.00
- HSBC Euro Note — XS4444444444 — Bid: 96.50, Ask: 99.75
- UBS Tech Autocall — XS5555555555 — Bid: 98.00, Ask: 101.00

**Pre-seeded Trades (3):**

- 2 confirmed buy orders (status=`"CONFIRMED"`)
- 1 pending order (status=`"PENDING"`)

**GET /rfq/{product_ref} response:**

```json
{
  "product_ref": 1,
  "isin": "XS1111111111",
  "description": "JPMorgan FTSE 100 Autocall",
  "price": 101.25,
  "valid_for_seconds": 30
}
```

The frontend shows a 30-second countdown after receiving the quote. If the user doesn't submit within 30s, the form resets and requires a fresh quote.

---

## Auth Design

- Algorithm: **HS256**
- Secret: hardcoded (`DEMO_SECRET_KEY = "verto-demo-secret"`)
- Token expiry: **30 minutes** (`exp = now + timedelta(minutes=30)`)
- Claims: `sub` (username), `exp`, `usertype`
- On expiry: API returns 401; frontend shows "Session expired, please log in again"
- No refresh token — re-login to get a new token

---

## Models (separate files)

**models/user.py**: id, username, password, usertype
**models/product.py**: ref, isin, description, bank, bid, ask, market_end_time
**models/trade.py**: id, trade_ref, product_ref, user_id, buy_sell, quantity, price, notional (calculated: quantity × price), status (String: `"PENDING"` | `"CONFIRMED"`), created_at

---

## Implementation Todos

1. `backend-skeleton` — database.py (SQLite async), models.py, main.py skeleton
2. `seed` — seed.py: 1 user, 5 products, 3 trades
3. `auth` — auth.py JWT helpers + routers/auth.py (POST /token)
4. `router-products` — routers/products.py (GET /products)
5. `router-rfq` — routers/rfq.py (GET /rfq/{product_ref})
6. `router-trades` — routers/trades.py (GET /orders, POST /trade)
7. `requirements` — requirements.txt
8. `frontend-html` — static/index.html (login + products + trade form + orders)
9. `readme` — README.md (setup in 3 commands, demo credentials)

---

## Virtual Environment

The app runs inside a Python `venv` for local development. `.venv/` lives inside `backend/` and is never committed (added to `.gitignore`).

---

## Quick Start (target)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Open http://localhost:8000
# Login: demo_client / demo123  or  demo_bank / demo123
```
