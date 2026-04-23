from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, merchants, orders, payments, webhooks, reconciliation

app = FastAPI(title="QR-SaaS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}


app.include_router(auth.router)
app.include_router(merchants.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(reconciliation.router)
