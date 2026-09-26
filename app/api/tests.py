from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.test import DiagnosticTest
from app.schemas.test import DiagnosticTestResponse

router = APIRouter(prefix="/tests", tags=["Diagnostic Tests"])


@router.get("", response_model=list[DiagnosticTestResponse])
async def list_tests(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiagnosticTest).order_by(DiagnosticTest.id)
    )

    return result.scalars().all()