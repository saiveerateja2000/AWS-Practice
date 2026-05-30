import os

from flask import g, jsonify

from service_base import create_service_app, downstream_get

SERVICE_NAME = os.getenv("SERVICE_NAME", "order-service")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000/profile")
app = create_service_app(SERVICE_NAME, "#0077cc")


@app.get("/details")
def order_details():
    status_code, downstream = downstream_get(USER_SERVICE_URL, g.request_id)
    return (
        jsonify(
            {
                "service": SERVICE_NAME,
                "request_id": g.request_id,
                "downstream_service": "user-service",
                "downstream_status": status_code,
                "downstream_response": downstream,
            }
        ),
        200 if status_code < 500 else 503,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
