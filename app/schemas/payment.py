from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    status: str
    provider_event_id: str | None = None

    model_config = ConfigDict(from_attributes=True)