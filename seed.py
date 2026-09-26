import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.centre import CentreTest, DiagnosticCentre
from app.models.test import DiagnosticTest


async def seed():
    async with AsyncSessionLocal() as db:

        # Check whether data already exists
        existing_test = await db.execute(
            select(DiagnosticTest).limit(1)
        )

        if existing_test.scalar_one_or_none():
            print("Seed data already exists.")
            return

        # -------------------------
        # Diagnostic Tests
        # -------------------------
        blood_test = DiagnosticTest(
            name="Complete Blood Count",
            price=Decimal("500.00"),
        )

        lipid_test = DiagnosticTest(
            name="Lipid Profile",
            price=Decimal("800.00"),
        )

        thyroid_test = DiagnosticTest(
            name="Thyroid Profile",
            price=Decimal("700.00"),
        )

        db.add_all([
            blood_test,
            lipid_test,
            thyroid_test,
        ])

        await db.flush()

        # -------------------------
        # Diagnostic Centres
        # -------------------------
        centre_one = DiagnosticCentre(
            name="Apollo Diagnostics",
            location="Noida",
        )

        centre_two = DiagnosticCentre(
            name="Max Diagnostics",
            location="Ghaziabad",
        )

        db.add_all([
            centre_one,
            centre_two,
        ])

        await db.flush()

        # -------------------------
        # Centre/Test mappings
        # -------------------------
        db.add_all([
            CentreTest(
                centre_id=centre_one.id,
                test_id=blood_test.id,
                price=Decimal("500.00"),
            ),
            CentreTest(
                centre_id=centre_one.id,
                test_id=lipid_test.id,
                price=Decimal("750.00"),
            ),
            CentreTest(
                centre_id=centre_two.id,
                test_id=blood_test.id,
                price=Decimal("450.00"),
            ),
            CentreTest(
                centre_id=centre_two.id,
                test_id=thyroid_test.id,
                price=Decimal("650.00"),
            ),
        ])

        await db.commit()

        print("Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())