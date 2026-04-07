# Verto Trading Demo

A minimal showcase of the Verto trading platform: **Login → Browse Products → Place a Trade → View Your Orders**.

Built with FastAPI, SQLite (in-memory), and a single plain HTML page. No build toolchain, no Docker.

---

## What this demonstrates

This project simulates a simplified trading workflow:

- User authentication
- Product discovery with bid/ask pricing
- RFQ (Request for Quote)
- Trade execution
- Order tracking

It is inspired by real-world financial systems and demonstrates
how legacy trading platforms can be redesigned using modern APIs.

---

## Quick Start

```bash
cd backend

# 1 — create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2 — install dependencies
pip install -r requirements.txt

# 3 — run the server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Demo credentials

| Username     | Password |
|--------------|----------|
| demo_client  | demo123  |
| demo_bank    | demo123  |

---

## API Endpoints

| Method | Path                  | Auth? | Description                          |
|--------|-----------------------|-------|--------------------------------------|
| POST   | `/token`              | No    | Login — returns JWT access token     |
| GET    | `/products`           | Yes   | List products with bid/ask           |
| GET    | `/rfq/{product_ref}`  | Yes   | Live quote (price + 30s validity)    |
| GET    | `/orders`             | Yes   | List your trades                     |
| POST   | `/trade`              | Yes   | Place a new trade                    |

All protected endpoints use `Authorization: Bearer <token>`.

---

## Notes

- Database is **in-memory SQLite** — data resets on every restart.
- `.venv/` is excluded from version control via `backend/.gitignore`.
- No refresh token — re-login after the 30-minute token expiry.
