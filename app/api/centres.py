from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.centre import CentreTest, DiagnosticCentre
from app.models.test import DiagnosticTest
from app.schemas.centre import (
    CentreTestResponse,
    DiagnosticCentreResponse,
)

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres"])


@router.get("", response_model=list[DiagnosticCentreResponse])
async def list_centres(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiagnosticCentre).order_by(DiagnosticCentre.id)
    )

    centres = result.scalars().all()

    response = []

    for centre in centres:
        test_result = await db.execute(
            select(
                CentreTest.test_id,
                DiagnosticTest.name,
                CentreTest.price,
            )
            .join(
                DiagnosticTest,
                DiagnosticTest.id == CentreTest.test_id,
            )
            .where(CentreTest.centre_id == centre.id)
            .order_by(CentreTest.test_id)
        )

        tests = [
            CentreTestResponse(
                test_id=row.test_id,
                test_name=row.name,
                price=row.price,
            )
            for row in test_result.all()
        ]

        response.append(
            DiagnosticCentreResponse(
                id=centre.id,
                name=centre.name,
                location=centre.location,
                tests=tests,
            )
        )

    return response


@router.get("/{centre_id}", response_model=DiagnosticCentreResponse)
async def get_centre(
    centre_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiagnosticCentre).where(
            DiagnosticCentre.id == centre_id
        )
    )

    centre = result.scalar_one_or_none()

    if centre is None:
        raise HTTPException(
            status_code=404,
            detail="Diagnostic centre not found",
        )

    test_result = await db.execute(
        select(
            CentreTest.test_id,
            DiagnosticTest.name,
            CentreTest.price,
        )
        .join(
            DiagnosticTest,
            DiagnosticTest.id == CentreTest.test_id,
        )
        .where(CentreTest.centre_id == centre.id)
        .order_by(CentreTest.test_id)
    )

    tests = [
        CentreTestResponse(
            test_id=row.test_id,
            test_name=row.name,
            price=row.price,
        )
        for row in test_result.all()
    ]

    return DiagnosticCentreResponse(
        id=centre.id,
        name=centre.name,
        location=centre.location,
        tests=tests,
    )