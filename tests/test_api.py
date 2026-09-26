import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models.webhook import WebhookEvent


# ============================================================
# Test Database Cleanup
# ============================================================


@pytest_asyncio.fixture(autouse=True)
async def clean_webhook_events():
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(WebhookEvent).where(
                WebhookEvent.event_id.like("pytest_webhook_%")
            )
        )
        await db.commit()

    yield

    await engine.dispose()


# ============================================================
# Helper Functions
# ============================================================


async def get_auth_headers(
    client: AsyncClient,
    email: str,
    password: str,
):
    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


async def create_test_booking(
    client: AsyncClient,
    headers: dict,
    appointment_datetime: str,
):
    response = await client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": 1,
            "centre_id": 1,
            "appointment_datetime": appointment_datetime,
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# Authentication Tests
# ============================================================


@pytest.mark.asyncio
async def test_signup():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/auth/signup",
            json={
                "email": "pytest_user@example.com",
                "password": "password123",
                "name": "Pytest User",
            },
        )

    assert response.status_code in {201, 400}

    if response.status_code == 201:
        data = response.json()

        assert data["email"] == "pytest_user@example.com"
        assert data["name"] == "Pytest User"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/auth/login",
            json={
                "email": "pytest_user@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/auth/login",
            json={
                "email": "pytest_user@example.com",
                "password": "wrongpassword",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get("/auth/me")

    assert response.status_code == 401


# ============================================================
# Diagnostic Tests API
# ============================================================


@pytest.mark.asyncio
async def test_list_tests():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get("/tests")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert "id" in data[0]
    assert "name" in data[0]
    assert "price" in data[0]


# ============================================================
# Diagnostic Centre API
# ============================================================


@pytest.mark.asyncio
async def test_list_centres():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get("/centres")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert "id" in data[0]
    assert "name" in data[0]
    assert "location" in data[0]
    assert "tests" in data[0]


@pytest.mark.asyncio
async def test_get_centre():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get("/centres/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert "name" in data
    assert "location" in data
    assert "tests" in data


@pytest.mark.asyncio
async def test_get_nonexistent_centre():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get("/centres/99999")

    assert response.status_code == 404


# ============================================================
# Booking Tests
# ============================================================


@pytest.mark.asyncio
async def test_create_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.post(
            "/bookings",
            headers=headers,
            json={
                "test_id": 1,
                "centre_id": 1,
                "appointment_datetime": "2028-01-15T10:00:00Z",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["test_id"] == 1
    assert data["centre_id"] == 1
    assert data["amount"] == "500.00"
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_booking_with_past_date():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.post(
            "/bookings",
            headers=headers,
            json={
                "test_id": 1,
                "centre_id": 1,
                "appointment_datetime": "2020-01-01T10:00:00Z",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"


@pytest.mark.asyncio
async def test_create_booking_with_unavailable_test():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.post(
            "/bookings",
            headers=headers,
            json={
                "test_id": 3,
                "centre_id": 1,
                "appointment_datetime": "2028-02-15T10:00:00Z",
            },
        )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Selected test is not available at this diagnostic centre"
    )


@pytest.mark.asyncio
async def test_list_my_bookings():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.get(
            "/bookings",
            headers=headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for booking in data:
        assert "id" in booking
        assert "test_id" in booking
        assert "centre_id" in booking
        assert "amount" in booking
        assert "status" in booking


@pytest.mark.asyncio
async def test_get_own_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-03-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.get(
            f"/bookings/{booking_id}",
            headers=headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_nonexistent_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.get(
            "/bookings/999999",
            headers=headers,
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-04-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.patch(
            f"/bookings/{booking_id}/cancel",
            headers=headers,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["status"] == "CANCELLED"


# ============================================================
# Payment Tests
# ============================================================


@pytest.mark.asyncio
async def test_successful_payment_confirms_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-05-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.post(
            f"/payments/{booking_id}?outcome=SUCCESS",
            headers=headers,
        )

        assert response.status_code == 201

        payment = response.json()

        assert payment["booking_id"] == booking_id
        assert payment["amount"] == "500.00"
        assert payment["status"] == "SUCCESS"

        booking_response = await client.get(
            f"/bookings/{booking_id}",
            headers=headers,
        )

    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_failed_payment_fails_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-06-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.post(
            f"/payments/{booking_id}?outcome=FAILED",
            headers=headers,
        )

        assert response.status_code == 201

        payment = response.json()

        assert payment["booking_id"] == booking_id
        assert payment["amount"] == "500.00"
        assert payment["status"] == "FAILED"

        booking_response = await client.get(
            f"/bookings/{booking_id}",
            headers=headers,
        )

    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_duplicate_payment_returns_conflict():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-07-15T10:00:00Z",
        )

        booking_id = booking["id"]

        first_response = await client.post(
            f"/payments/{booking_id}?outcome=SUCCESS",
            headers=headers,
        )

        assert first_response.status_code == 201

        second_response = await client.post(
            f"/payments/{booking_id}?outcome=SUCCESS",
            headers=headers,
        )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Payment already exists for this booking"
    )


@pytest.mark.asyncio
async def test_payment_for_nonexistent_booking():
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        response = await client.post(
            "/payments/999999?outcome=SUCCESS",
            headers=headers,
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_payment_for_cancelled_booking():
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-08-15T10:00:00Z",
        )

        booking_id = booking["id"]

        cancel_response = await client.patch(
            f"/bookings/{booking_id}/cancel",
            headers=headers,
        )

        assert cancel_response.status_code == 200

        payment_response = await client.post(
            f"/payments/{booking_id}?outcome=SUCCESS",
            headers=headers,
        )

    assert payment_response.status_code == 400

    assert (
        payment_response.json()["detail"]
        == "Payment can only be initiated for a pending booking"
    )


# ============================================================
# Webhook Tests
# ============================================================


@pytest.mark.asyncio
async def test_successful_payment_webhook_confirms_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-09-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.post(
            "/webhooks/payment",
            json={
                "event_id": "pytest_webhook_success_001",
                "booking_id": booking_id,
                "status": "SUCCESS",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["event_id"] == "pytest_webhook_success_001"
        assert data["booking_id"] == booking_id
        assert data["status"] == "SUCCESS"

        booking_response = await client.get(
            f"/bookings/{booking_id}",
            headers=headers,
        )

    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_failed_payment_webhook_fails_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-10-15T10:00:00Z",
        )

        booking_id = booking["id"]

        response = await client.post(
            "/webhooks/payment",
            json={
                "event_id": "pytest_webhook_failed_001",
                "booking_id": booking_id,
                "status": "FAILED",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["event_id"] == "pytest_webhook_failed_001"
        assert data["booking_id"] == booking_id
        assert data["status"] == "FAILED"

        booking_response = await client.get(
            f"/bookings/{booking_id}",
            headers=headers,
        )

    assert booking_response.status_code == 200
    assert booking_response.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_duplicate_webhook_is_idempotent():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-11-15T10:00:00Z",
        )

        booking_id = booking["id"]

        payload = {
            "event_id": "pytest_webhook_duplicate_001",
            "booking_id": booking_id,
            "status": "SUCCESS",
        }

        first_response = await client.post(
            "/webhooks/payment",
            json=payload,
        )

        second_response = await client.post(
            "/webhooks/payment",
            json=payload,
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["message"] == "Webhook processed successfully"

    assert second_data["message"] == "Webhook already processed"

    assert second_data["event_id"] == payload["event_id"]
    assert second_data["booking_id"] == booking_id
    assert second_data["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_webhook_for_nonexistent_booking():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhooks/payment",
            json={
                "event_id": "pytest_webhook_invalid_booking_001",
                "booking_id": 999999,
                "status": "SUCCESS",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_webhook_with_invalid_status():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhooks/payment",
            json={
                "event_id": "pytest_webhook_invalid_status_001",
                "booking_id": 1,
                "status": "INVALID",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payment status"
    # ============================================================
# Webhook Concurrency Test
# ============================================================


@pytest.mark.asyncio
async def test_concurrent_duplicate_webhooks_are_idempotent():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        headers = await get_auth_headers(
            client,
            "pytest_user@example.com",
            "password123",
        )

        booking = await create_test_booking(
            client,
            headers,
            "2028-12-15T10:00:00Z",
        )

        booking_id = booking["id"]

        payload = {
            "event_id": "pytest_webhook_concurrent_001",
            "booking_id": booking_id,
            "status": "SUCCESS",
        }

        response_1, response_2 = await asyncio.gather(
            client.post(
                "/webhooks/payment",
                json=payload,
            ),
            client.post(
                "/webhooks/payment",
                json=payload,
            ),
        )

        responses = [response_1, response_2]

        assert all(
            response.status_code == 200
            for response in responses
        )

        messages = {
            response.json()["message"]
            for response in responses
        }

        assert messages == {
            "Webhook processed successfully",
            "Webhook already processed",
        }