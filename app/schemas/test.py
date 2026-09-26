from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DiagnosticTestResponse(BaseModel):
    id: int
    name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)