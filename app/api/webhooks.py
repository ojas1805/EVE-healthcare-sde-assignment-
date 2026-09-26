from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook import WebhookEvent, WebhookPaymentStatus
from app.schemas.webhook import (
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post(
    "/payment",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
)
async def payment_webhook(
    data: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    # ------------------------------------------------------------
    # 1. Validate webhook status
    # ------------------------------------------------------------

    if data.status not in {"SUCCESS", "FAILED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment status",
        )

    webhook_status = WebhookPaymentStatus(data.status)

    payment_status = (
        PaymentStatus.SUCCESS
        if data.status == "SUCCESS"
        else PaymentStatus.FAILED
    )

    # ------------------------------------------------------------
    # 2. Check that the booking exists
    # ------------------------------------------------------------

    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == data.booking_id
        )
    )

    booking = booking_result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # ------------------------------------------------------------
    # 3. Atomically register the webhook event
    # ------------------------------------------------------------

    webhook_insert = (
        insert(WebhookEvent)
        .values(
            event_id=data.event_id,
            booking_id=booking.id,
            status=webhook_status,
        )
        .on_conflict_do_nothing(
            index_elements=[WebhookEvent.event_id]
        )
        .returning(WebhookEvent.id)
    )

    result = await db.execute(webhook_insert)

    inserted_event_id = result.scalar_one_or_none()

    # ------------------------------------------------------------
    # 4. Duplicate webhook
    # ------------------------------------------------------------

    if inserted_event_id is None:
        await db.rollback()

        existing_event_result = await db.execute(
            select(
                WebhookEvent.booking_id,
                WebhookEvent.status,
            ).where(
                WebhookEvent.event_id == data.event_id
            )
        )

        existing_event = existing_event_result.one()

        return PaymentWebhookResponse(
            message="Webhook already processed",
            event_id=data.event_id,
            booking_id=existing_event.booking_id,
            status=existing_event.status.value,
        )

    # ------------------------------------------------------------
    # 5. Lock the booking row
    # ------------------------------------------------------------

    booking_result = await db.execute(
        select(Booking)
        .where(Booking.id == data.booking_id)
        .with_for_update()
    )

    booking = booking_result.scalar_one()

    # ------------------------------------------------------------
    # 6. Find existing payment
    # ------------------------------------------------------------

    payment_result = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking.id
        )
    )

    payment = payment_result.scalar_one_or_none()

    # ------------------------------------------------------------
    # 7. Create or update payment
    # ------------------------------------------------------------

    if payment is None:
        payment = Payment(
            booking_id=booking.id,
            amount=booking.amount,
            status=payment_status,
            provider_event_id=data.event_id,
        )

        db.add(payment)

    else:
        payment.status = payment_status
        payment.provider_event_id = data.event_id

    # ------------------------------------------------------------
    # 8. Update booking status
    # ------------------------------------------------------------

    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    # ------------------------------------------------------------
    # 9. Commit everything atomically
    # ------------------------------------------------------------

    await db.commit()

    # ------------------------------------------------------------
    # 10. Return success
    # ------------------------------------------------------------

    return PaymentWebhookResponse(
        message="Webhook processed successfully",
        event_id=data.event_id,
        booking_id=booking.id,
        status=data.status,
    )