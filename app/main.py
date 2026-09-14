from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_all_tables
from app.routers import auth, users, whatsapp, schedules, subscription

app = FastAPI(
    title="Notify WA API",
    description="Backend for the Notify WA WhatsApp message-scheduling app (demo build).",
    version="0.1.0",
)

# Wide-open CORS for local development with the Flutter app / emulator.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Database + all tables are created automatically here - nothing to
    # click in pgAdmin4 beyond having PostgreSQL running with the
    # credentials from .env.
    create_all_tables()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(whatsapp.router)
app.include_router(schedules.router)
app.include_router(subscription.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Notify WA API"}
