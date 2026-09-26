from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.bookings import router as bookings_router
from app.api.centres import router as centres_router
from app.api.payments import router as payments_router
from app.api.tests import router as tests_router
from app.api.webhooks import router as webhooks_router


app = FastAPI(
    title="Diagnostic Test Booking API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(centres_router)
app.include_router(tests_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}