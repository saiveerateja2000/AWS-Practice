import os

from flask import g, jsonify

from service_base import create_service_app

SERVICE_NAME = os.getenv("SERVICE_NAME", "inventory-service")
app = create_service_app(SERVICE_NAME, "#7b2cbf")
app.config["SIMULATE_FAILURE"] = False


@app.get("/inventory/check")
def inventory_check():
    if app.config["SIMULATE_FAILURE"]:
        return (
            jsonify(
                {
                    "service": SERVICE_NAME,
                    "request_id": g.request_id,
                    "status": "unavailable",
                    "message": "Simulated failure enabled",
                }
            ),
            503,
        )

    return jsonify(
        {
            "service": SERVICE_NAME,
            "request_id": g.request_id,
            "inventory": {
                "sku": "sku-1001",
                "available": True,
                "quantity": 42,
            },
        }
    )


@app.get("/simulate-failure")
def simulate_failure():
    app.config["SIMULATE_FAILURE"] = True
    return (
        jsonify(
            {
                "service": SERVICE_NAME,
                "request_id": g.request_id,
                "status": "unavailable",
                "message": "Failure simulation enabled",
            }
        ),
        503,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
