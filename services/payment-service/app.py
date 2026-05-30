import os

from flask import g, jsonify

from service_base import create_service_app, downstream_get

SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:5000/inventory/check")
app = create_service_app(SERVICE_NAME, "#f08c00")


@app.get("/payments/process")
def payment_process():
    status_code, inventory_response = downstream_get(INVENTORY_SERVICE_URL, g.request_id)
    success = status_code == 200
    return (
        jsonify(
            {
                "service": SERVICE_NAME,
                "request_id": g.request_id,
                "payment_status": "processed" if success else "pending_inventory",
                "downstream_service": "inventory-service",
                "downstream_status": status_code,
                "downstream_response": inventory_response,
                "message": "Gracefully handled inventory availability",
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
