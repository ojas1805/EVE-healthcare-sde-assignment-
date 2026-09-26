from pydantic import BaseModel


class PaymentWebhookRequest(BaseModel):
    event_id: str
    booking_id: int
    status: str


class PaymentWebhookResponse(BaseModel):
    message: str
    event_id: str
    booking_id: int
    status: str