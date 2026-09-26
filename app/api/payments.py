from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


class PaymentOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@router.post(
    "/{booking_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    booking_id: int,
    outcome: PaymentOutcome = Query(PaymentOutcome.SUCCESS),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Find the booking belonging to the current user
    # ---------------------------------------------------------
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
    )

    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # ---------------------------------------------------------
    # 2. Check whether a payment already exists
    # ---------------------------------------------------------
    existing_payment_result = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking.id
        )
    )

    existing_payment = existing_payment_result.scalar_one_or_none()

    if existing_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already exists for this booking",
        )

    # ---------------------------------------------------------
    # 3. Payment can only be initiated for PENDING bookings
    # ---------------------------------------------------------
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment can only be initiated for a pending booking",
        )

    # ---------------------------------------------------------
    # 4. Determine payment result
    # ---------------------------------------------------------
    if outcome == PaymentOutcome.SUCCESS:
        payment_status = PaymentStatus.SUCCESS
    else:
        payment_status = PaymentStatus.FAILED

    # ---------------------------------------------------------
    # 5. Create payment
    # ---------------------------------------------------------
    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_status,
    )

    db.add(payment)

    # ---------------------------------------------------------
    # 6. Update booking status
    # ---------------------------------------------------------
    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    # ---------------------------------------------------------
    # 7. Save both changes
    # ---------------------------------------------------------
    await db.commit()

    # ---------------------------------------------------------
    # 8. Refresh payment so generated fields are available
    # ---------------------------------------------------------
    await db.refresh(payment)

    return payment