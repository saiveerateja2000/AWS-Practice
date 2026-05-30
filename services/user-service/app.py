import os

from flask import g, jsonify

from service_base import create_service_app

SERVICE_NAME = os.getenv("SERVICE_NAME", "user-service")
app = create_service_app(SERVICE_NAME, "#2f9e44")


@app.get("/users/profile")
def user_profile():
    return jsonify(
        {
            "service": SERVICE_NAME,
            "request_id": g.request_id,
            "user": {
                "id": "u-1001",
                "name": "Cloud User",
                "tier": "standard",
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
