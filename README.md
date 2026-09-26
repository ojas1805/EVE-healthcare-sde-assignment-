# Diagnostic Test Booking API

A production-style asynchronous REST API for booking diagnostic tests, handling simulated payments, and processing idempotent payment webhooks.

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT Authentication
- Passlib + bcrypt
- pytest + pytest-asyncio + httpx
- Docker + Docker Compose

## Features

### Authentication

- User signup
- User login
- JWT-based authentication
- Password hashing using bcrypt
- Protected user endpoints

### Diagnostic Tests

- List available diagnostic tests
- List diagnostic centres
- View a diagnostic centre and its available tests
- Centre-specific test pricing

### Bookings

- Create a diagnostic test booking
- Validate appointment time
- Validate test availability at a centre
- View user's bookings
- View an individual booking
- Cancel pending or confirmed bookings
- Booking ownership protection

### Payments

- Simulated payment processing
- SUCCESS and FAILED payment outcomes
- Payment amount taken from the booking
- Duplicate payment protection
- Booking status updated after payment

### Payment Webhooks

- Payment webhook endpoint
- SUCCESS and FAILED webhook handling
- Idempotent webhook processing
- Database uniqueness constraint on `event_id`
- PostgreSQL `ON CONFLICT DO NOTHING`
- Row-level booking locking using `SELECT ... FOR UPDATE`
- Concurrent duplicate webhook protection

## Database Schema

The application uses the following tables:

- `users`
- `diagnostic_centres`
- `diagnostic_tests`
- `centre_tests`
- `bookings`
- `payments`
- `webhook_events`

Alembic is used for database migrations.

## Project Structure

```text
diagnostic-booking-api/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── bookings.py
│   │   ├── centres.py
│   │   ├── payments.py
│   │   ├── tests.py
│   │   └── webhooks.py
│   │
│   ├── dependencies/
│   │   └── auth.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── centre.py
│   │   ├── test.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── webhook.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── centre.py
│   │   ├── test.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── webhook.py
│   │
│   ├── services/
│   │   └── auth.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── alembic/
│   └── versions/
│
├── tests/
│   └── test_api.py
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── seed.py
├── pytest.ini
└── README.md