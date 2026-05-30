import json
import logging
import os
import socket
import threading
import time
import uuid
from datetime import datetime, timezone

import psutil
import requests
from flask import Flask, g, jsonify, request


def _hostname() -> str:
    return socket.gethostname()


def _ip_address() -> str:
    try:
        return socket.gethostbyname(_hostname())
    except OSError:
        return "127.0.0.1"


def _container_id() -> str:
    try:
        with open("/proc/self/cgroup", "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip().split("/")[-1]
                if item and len(item) >= 12:
                    return item[:12]
    except OSError:
        pass
    return _hostname()[:12]


def _runtime(service_name: str) -> dict:
    process = psutil.Process(os.getpid())
    return {
        "service": service_name,
        "hostname": _hostname(),
        "ip_address": _ip_address(),
        "container_id": _container_id(),
        "environment": os.getenv("ENVIRONMENT", "local"),
        "aws_deployment_type": os.getenv("AWS_DEPLOYMENT_TYPE", "local"),
        "version": os.getenv("VERSION", "1.0.0"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.05),
        "memory_percent": psutil.virtual_memory().percent,
        "process_memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
    }


def _configure_logger(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.propagate = False
    return logger


def create_service_app(service_name: str, color: str) -> Flask:
    app = Flask(service_name)
    app.config["SERVICE_NAME"] = service_name
    app.config["THEME_COLOR"] = color
    app.config["REQUEST_COUNT"] = 0
    app.config["PATH_COUNTS"] = {}
    app.config["COUNTER_LOCK"] = threading.Lock()
    app.logger = _configure_logger(service_name)

    @app.before_request
    def before_request():
        g.start_time = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        with app.config["COUNTER_LOCK"]:
            app.config["REQUEST_COUNT"] += 1
            app.config["PATH_COUNTS"][request.path] = app.config["PATH_COUNTS"].get(request.path, 0) + 1

    @app.after_request
    def after_request(response):
        elapsed_ms = round((time.perf_counter() - g.start_time) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": g.request_id,
            "service": service_name,
            "hostname": _hostname(),
            "source_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "path": request.path,
            "method": request.method,
            "status": response.status_code,
            "response_time_ms": elapsed_ms,
        }
        app.logger.info(json.dumps(payload))
        return response

    @app.get("/")
    def index():
        info = _runtime(service_name)
        return f"""
<!doctype html>
<html>
<head><title>{service_name}</title></head>
<body style=\"font-family:Arial;background:{color};color:white;padding:24px\">
<h1>{service_name}</h1>
<p><strong>Request ID:</strong> {g.request_id}</p>
<pre>{json.dumps(info, indent=2)}</pre>
</body>
</html>
"""

    @app.get("/system-info")
    def system_info():
        return jsonify(_runtime(service_name))

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "service": service_name,
                "hostname": _hostname(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.get("/metrics")
    def metrics():
        runtime = _runtime(service_name)
        with app.config["COUNTER_LOCK"]:
            runtime.update(
                {
                    "request_count": app.config["REQUEST_COUNT"],
                    "path_counts": dict(app.config["PATH_COUNTS"]),
                }
            )
        return jsonify(runtime)

    @app.get("/lbtest")
    def lbtest():
        return jsonify(
            {
                "hostname": _hostname(),
                "container_id": _container_id(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": g.request_id,
            }
        )

    return app


def downstream_get(url: str, request_id: str, timeout: float = 3.0):
    try:
        response = requests.get(url, headers={"X-Request-ID": request_id}, timeout=timeout)
        data = response.json() if response.content else {}
        return response.status_code, data
    except requests.RequestException:
        return 503, {"status": "error", "message": "Downstream service unavailable"}
