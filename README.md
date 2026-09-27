# Diagnostic Test Booking API

A backend API for booking diagnostic tests, managing appointments, and processing simulated payments.

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT authentication
- bcrypt password hashing
- pytest + httpx
- Docker + Docker Compose

---

## Features

- User signup and login
- JWT-based authentication
- View diagnostic tests
- View diagnostic centres and centre-specific test prices
- Create and manage bookings
- Cancel pending/confirmed bookings
- Simulated payment processing
- Payment success/failure handling
- Payment webhook processing
- Idempotent webhook handling
- Concurrent duplicate webhook protection
- PostgreSQL persistence
- Alembic database migrations
- Automated API tests
- Dockerized API and PostgreSQL

---

# 1. How to Run Locally

## Prerequisites

Install:

- Python 3.12+
- PostgreSQL 16+
- Git

Clone the repository:

```bash
git clone https://github.com/ojas1805/EVE-healthcare-sde-assignment-.git
cd EVE-healthcare-sde-assignment-
## Running Locally

### Prerequisites

- Python 3.12+
- Docker Desktop
- Git

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd EVE-healthcare-sde-assignment-

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate


Then:

```markdown
### 3. Install dependencies

```bash
pip install -r requirements.txt
docker compose up -d postgres
docker compose ps
alembic upgrade head
python seed.py


---

#### 2. API Endpoints + Examples

Add a concise table:

```markdown
## API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Register a user |
| POST | `/auth/login` | No | Login and receive JWT |
| GET | `/auth/me` | Yes | Get current user |
| GET | `/tests` | No | List diagnostic tests |
| GET | `/centres` | No | List diagnostic centres |
| GET | `/centres/{centre_id}` | No | Get centre details |
| POST | `/bookings` | Yes | Create booking |
| GET | `/bookings` | Yes | List user's bookings |
| GET | `/bookings/{booking_id}` | Yes | Get booking |
| POST | `/bookings/{booking_id}/cancel` | Yes | Cancel booking |
| POST | `/payments/{booking_id}` | Yes | Process simulated payment |
| POST | `/webhooks/payment` | No | Process payment webhook |

### Signup

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "Test User"
  }'


---

#### 3. Database / Schema Design

Your current list of tables is **not enough** for "Database/schema design."

Add:

```markdown
## Database Schema Design

### Users

- `id` - Primary key
- `email` - Unique user email
- `password_hash` - Bcrypt password hash
- `name`
- `created_at`

### Diagnostic Tests

- `id` - Primary key
- `name`
- `price`

### Diagnostic Centres

- `id` - Primary key
- `name`
- `location`

### Centre Tests

- `id` - Primary key
- `centre_id` - Foreign key to diagnostic centres
- `test_id` - Foreign key to diagnostic tests
- `price`

A unique constraint on `(centre_id, test_id)` prevents duplicate mappings.

### Bookings

- `id` - Primary key
- `user_id` - Foreign key to users
- `test_id` - Foreign key to diagnostic tests
- `centre_id` - Foreign key to diagnostic centres
- `appointment_datetime`
- `amount`
- `status`
- `created_at`
- `updated_at`

### Payments

- `id` - Primary key
- `booking_id` - Unique foreign key to bookings
- `amount`
- `status`
- `provider_event_id`
- `created_at`

### Webhook Events

- `id` - Primary key
- `event_id` - Unique webhook event identifier
- `booking_id` - Foreign key to bookings
- `status`
- `received_at`

### Relationships

User → Bookings

Diagnostic Centre → Centre Tests ← Diagnostic Test

User → Booking → Payment

Booking → Webhook Events

## Important Assumptions

- Payments are simulated; no real payment gateway is integrated.
- A booking stores the selected centre-specific price at booking time.
- Appointment time must be in the future.
- A test must be available at the selected diagnostic centre before a booking can be created.
- `event_id` is assumed to uniquely identify a payment-provider webhook event.
- JWT is used for stateless API authentication.
- Users can access only their own bookings.
- The current implementation does not model real-time appointment-slot inventory.
- PostgreSQL is the target database.

## What I Would Improve With More Time

### Real Payment Integration

Integrate a real payment provider such as Razorpay or Stripe, including webhook signature verification.

### Appointment Slot Management

Introduce appointment slots and capacity management to prevent multiple users from booking the same slot.

### Stronger Webhook Security

Verify webhook signatures before processing payment events.

### Production Configuration

Use a proper secret-management solution instead of development environment secrets.

### Observability

Add structured logging, request IDs, metrics, and error monitoring.

### CI/CD

Add GitHub Actions to automatically run tests, migrations checks, and Docker builds.

### Additional Testing

Add more concurrency, failure-recovery, and database integration tests.