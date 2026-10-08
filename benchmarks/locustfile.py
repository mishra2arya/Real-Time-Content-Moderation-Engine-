"""Locust load test scenario for real-time moderation engine."""

import random

from locust import HttpUser, between, task

TEST_PAYLOADS = [
    {
        "text": "Have a wonderful morning, thanks for the helpful answer!",
        "strict": False,
    },
    {"text": "You are a complete idiot and should be banned forever.", "strict": False},
    {"text": "I will find your address and beat you up.", "strict": False},
    {"text": "Please kill -9 the hung background process.", "strict": False},
    {
        "text": "Congratulations on the awesome project milestone release!",
        "strict": False,
    },
    {
        "text": "Your country is full of subhuman thieves and degenerates.",
        "strict": False,
    },
    {"text": "That rock concert performance was absolutely sick!", "strict": False},
    {"text": "Can someone share the documentation link for the API?", "strict": False},
]


class ModerationUser(HttpUser):
    """Simulates high-throughput client sending moderation requests."""

    wait_time = between(0.01, 0.05)

    @task(8)
    def test_moderate_single(self):
        """Send single moderation request."""
        sample = random.choice(TEST_PAYLOADS)
        payload = {
            "text": sample["text"],
            "text_id": f"locust-{random.randint(10000, 99999)}",
            "strict": sample["strict"],
        }
        with self.client.post(
            "/moderate", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}: {response.text}")

    @task(2)
    def test_moderate_batch(self):
        """Send batched moderation request."""
        batch = random.sample(TEST_PAYLOADS, k=random.randint(2, 5))
        payload = {
            "items": [
                {
                    "text": it["text"],
                    "text_id": f"locust-b-{random.randint(1000, 9999)}",
                }
                for it in batch
            ],
            "strict": False,
        }
        with self.client.post(
            "/moderate/batch", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}: {response.text}")

    @task(1)
    def test_health(self):
        """Send health check probe."""
        self.client.get("/health")
