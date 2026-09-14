# Notify WA — Backend (FastAPI + PostgreSQL + SQLAlchemy)

This is the backend for **Notify WA**, a WhatsApp reminder-scheduling app.
It has been built and **tested end-to-end against a real local PostgreSQL
instance** (register → login → connect WhatsApp (demo) → create schedule →
home summary → subscription plans → PayHere init → bank transfer upload —
all verified working).

## 1. Prerequisites

- Python 3.10+
- PostgreSQL installed locally, with pgAdmin4
- In pgAdmin4 (or `psql`), make sure the `postgres` superuser's password is
  `admin123` (or update `.env` to match whatever you actually set):

  ```sql
  ALTER USER postgres PASSWORD 'admin123';
  ```

You do **not** need to manually create the `notify_wa_db` database — the
app does this automatically the first time it starts (see `app/database.py`).

## 2. Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit values if your local setup differs
```

## 3. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first run you'll see in the console:

```
[db-init] Created database 'notify_wa_db'.
[db-init] Tables verified/created.
```

Open http://localhost:8000/docs for the interactive Swagger UI (every
endpoint below is listed there with a "Try it out" button).

## 4. What's implemented

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login` (JWT) |
| Users | `GET /api/users/me`, `GET /api/users/me/home-summary` |
| WhatsApp (demo) | `POST /api/whatsapp/connect`, `GET /api/whatsapp/groups` |
| Schedules | `POST/GET /api/schedules`, `PUT/DELETE /api/schedules/{id}` |
| Subscription | `GET /api/subscription/plans`, `GET /api/subscription/bank-details`, `POST /api/subscription/payhere/init`, `POST /api/subscription/payhere/notify`, `POST /api/subscription/bank-transfer` |

### About the WhatsApp integration (important)

This build is a **demo**, exactly as discussed: `app/services/whatsapp_service.py`
returns realistic mock groups and pretends to send messages successfully.
No real WhatsApp account is contacted. When you're ready to go live:

1. Get access to the official **WhatsApp Business Cloud API** (Meta), get a
   phone number ID + access token.
2. Fill in `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN` in `.env`,
   set `WHATSAPP_DEMO_MODE=false`.
3. Replace the commented-out block in `send_whatsapp_message()` with a real
   call to Meta's Graph API.
4. Note: Meta's official API does not expose "list all my groups" — real
   integrations typically register each group/broadcast list once during
   a setup flow. `mock_groups_for_new_connection()` simulates the *result*
   of that flow for the UI; you'll want to replace it with your own
   registration screen when you connect the real API.

### About PayHere

`app/services/payhere_service.py` builds the MD5 hash PayHere's checkout
page requires and verifies the `notify_url` webhook signature. Put your
real `PAYHERE_MERCHANT_ID` / `PAYHERE_MERCHANT_SECRET` in `.env` (sandbox
values while testing, live values when you go live). The Flutter app
currently shows the generated order in a dialog as a placeholder — wire
`checkout_action_url` up to a WebView (or your payment page) to complete
the real checkout redirect.

### Uploaded bank-transfer receipts

Saved to `backend/uploads/receipts/`. Review manually and flip the
transaction's status + the user's plan (there's no admin UI for this yet —
easiest done via pgAdmin4 directly on the `payment_transactions` /
`users` tables, or add a small admin endpoint later).

## 5. Background sending (next step, not included)

Actually sending messages at their scheduled time needs a background
worker — `APScheduler` is already in `requirements.txt` for this. A
simple approach: a job that runs every minute, queries
`schedule_reminders` where `status='active'` and the scheduled time has
arrived, calls `send_whatsapp_message()`, writes a `MessageLog` row, and
advances `scheduled_date`/`scheduled_time` for recurring frequencies.
