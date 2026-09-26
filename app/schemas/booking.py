from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    test_id: int
    centre_id: int
    appointment_datetime: datetime


class BookingResponse(BaseModel):
    id: int
    test_id: int
    centre_id: int
    appointment_datetime: datetime
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)