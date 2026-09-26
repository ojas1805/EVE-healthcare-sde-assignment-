from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.booking import Booking, BookingStatus
from app.models.centre import CentreTest
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse


router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Appointment must be in the future
    now = datetime.now(timezone.utc)

    appointment_datetime = data.appointment_datetime

    # Handle naive datetimes safely
    if appointment_datetime.tzinfo is None:
        appointment_datetime = appointment_datetime.replace(
            tzinfo=timezone.utc
        )

    if appointment_datetime <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment time must be in the future",
        )

    # Check that this centre offers this test
    result = await db.execute(
        select(CentreTest).where(
            CentreTest.centre_id == data.centre_id,
            CentreTest.test_id == data.test_id,
        )
    )

    centre_test = result.scalar_one_or_none()

    if centre_test is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected test is not available at this diagnostic centre",
        )

    # Create booking using the centre-specific price
    booking = Booking(
        user_id=current_user.id,
        test_id=data.test_id,
        centre_id=data.centre_id,
        appointment_datetime=appointment_datetime,
        amount=centre_test.price,
        status=BookingStatus.PENDING,
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return booking
@router.get(
    "",
    response_model=list[BookingResponse],
)
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )

    return result.scalars().all()
@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    return booking
@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    if booking.status not in {
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking cannot be cancelled in its current status",
        )

    booking.status = BookingStatus.CANCELLED

    await db.commit()
    await db.refresh(booking)

    return booking