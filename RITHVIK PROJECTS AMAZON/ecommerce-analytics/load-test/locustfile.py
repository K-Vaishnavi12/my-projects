"""
Load test for the E-Commerce Analytics Platform.
Simulates realistic user traffic: 70% reads, 25% writes, 5% analytics queries.

Run:
  # via Docker (recommended - no python install needed):
  docker run -it --rm -p 8089:8089 -v "$(pwd):/mnt/locust" locustio/locust \
     -f /mnt/locust/locustfile.py --host http://host.docker.internal:80

  # then open http://localhost:8089
"""
import random
import uuid
from locust import HttpUser, task, between

PRODUCTS = [
    ("P001", "Kindle Paperwhite", 9999.00),
    ("P002", "USB-C Cable", 299.00),
    ("P003", "Echo Dot", 4999.00),
    ("P004", "Fire TV Stick", 3999.00),
]


class EcommerceUser(HttpUser):
    wait_time = between(0.05, 0.3)

    def on_start(self):
        self.user_id = f"user-{uuid.uuid4().hex[:8]}"
        self.created_orders = []

    @task(25)
    def create_order(self):
        items = random.sample(PRODUCTS, k=random.randint(1, 3))
        body = {
            "userId": self.user_id,
            "shippingAddress": "1 Load Test Street",
            "items": [
                {"productId": pid, "productName": name, "quantity": random.randint(1, 3), "price": price}
                for pid, name, price in items
            ],
        }
        with self.client.post("/api/v1/orders", json=body, name="POST /orders", catch_response=True) as r:
            if r.status_code == 201 or r.status_code == 200:
                try:
                    self.created_orders.append(r.json()["orderId"])
                    if len(self.created_orders) > 20:
                        self.created_orders.pop(0)
                except Exception:
                    pass
            elif r.status_code == 429:
                r.success()  # rate limit is expected under high load

    @task(70)
    def get_order(self):
        if not self.created_orders:
            return
        oid = random.choice(self.created_orders)
        self.client.get(f"/api/v1/orders/{oid}/user/{self.user_id}", name="GET /orders/{id}")

    @task(5)
    def analytics_summary(self):
        self.client.get("/api/v1/analytics/summary", name="GET /analytics/summary")
