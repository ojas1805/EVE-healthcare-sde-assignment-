from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CentreTestResponse(BaseModel):
    test_id: int
    test_name: str
    price: Decimal


class DiagnosticCentreResponse(BaseModel):
    id: int
    name: str
    location: str
    tests: list[CentreTestResponse] = []

    model_config = ConfigDict(from_attributes=True)