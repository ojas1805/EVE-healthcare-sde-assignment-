import asyncio

import httpx


URL = "http://127.0.0.1:8000/webhooks/payment"

PAYLOAD = {
    "event_id": "evt_concurrent_001",
    "booking_id": 8,
    "status": "SUCCESS",
}


async def send_webhook(client, request_number):
    response = await client.post(URL, json=PAYLOAD)

    print(f"Request {request_number}:")
    print("Status:", response.status_code)
    print("Response:", response.json())
    print()


async def main():
    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            send_webhook(client, 1),
            send_webhook(client, 2),
        )


if __name__ == "__main__":
    asyncio.run(main())