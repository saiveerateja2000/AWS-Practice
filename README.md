# Cloud Native Traffic Visualization Platform

A complete cloud-native Python microservices platform designed to run locally with Docker Compose and be deployable to Amazon ECS Fargate or Amazon EKS without application code changes.

## Tech Stack
- Python 3.11
- Flask
- HTML / CSS / JavaScript
- Docker / Docker Compose
- Nginx (path-based routing, ALB-like simulation)

## Project Structure

```text
.
├── docker-compose.yml
├── frontend/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       ├── graph.html
│       ├── health.html
│       ├── index.html
│       ├── loadtest.html
│       ├── system.html
│       └── traffic.html
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── service_base.py
│   ├── order-service/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── user-service/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   ├── payment-service/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   └── inventory-service/
│       ├── app.py
│       ├── Dockerfile
│       ├── requirements.txt
└── deploy/
    ├── ecs/
    │   ├── service-definitions.md
    │   └── task-definitions.json
    └── eks/
        ├── deployment.yaml
        ├── hpa.yaml
        ├── ingress.yaml
        ├── namespace.yaml
        └── service.yaml
```

## Microservices
- `order-service` (Blue theme)
- `user-service` (Green theme)
- `payment-service` (Orange theme)
- `inventory-service` (Purple theme)

Each service runs on port `5000` and provides:
- `/` service info page
- `/health`
- `/metrics`
- `/lbtest`
- `/system-info`

### Environment Variables
- `SERVICE_NAME`
- `ENVIRONMENT`
- `AWS_DEPLOYMENT_TYPE`
- `VERSION`

## Service Communication
- `order-service` -> `user-service` via `/details` (externally available as `/orders/details` through nginx)
- `payment-service` -> `inventory-service` via `/process` (externally available as `/payments/process` through nginx)

## Request Tracing and Logging
- Request ID generated for every incoming request (`X-Request-ID`)
- Request ID propagated to downstream service calls
- Structured JSON logs include timestamp, request ID, service name, hostname, source IP, path, and response time

## Health Endpoint Contract
```json
{
  "status": "healthy",
  "service": "service-name",
  "hostname": "hostname",
  "timestamp": "current-time"
}
```

## Traffic Dashboard
The frontend includes a traffic dashboard showing request totals for:
- Order Service Requests
- User Service Requests
- Payment Service Requests
- Inventory Service Requests

## Failure Simulation
- `inventory-service` endpoint: `/simulate-failure` (returns `503`)
- `payment-service` gracefully handles inventory failure in `/payments/process`

## Service Dependency Graph
- Order Service -> User Service
- Payment Service -> Inventory Service

## Observability-Ready Design
The code and endpoints are designed to support future integration with:
- OpenTelemetry
- Prometheus
- Grafana
- Jaeger

## Docker Requirements
Each service and frontend uses:
- `python:3.11-slim`

## Local Validation Guide

### Build
```bash
docker compose build
```

### Start
```bash
docker compose up -d
```

### Status
```bash
docker compose ps
```

### Logs
```bash
docker compose logs -f nginx order-service user-service payment-service inventory-service frontend
```

### Stop
```bash
docker compose down
```

### Validation Steps
1. Verify dashboard: open `http://localhost:8080`
2. Verify service communication:
   - `http://localhost:8080/orders/details`
   - `http://localhost:8080/payments/process`
3. Verify request tracing: check `X-Request-ID` response header and downstream payloads
4. Verify logging: inspect JSON logs from service containers
5. Verify health checks:
   - `/orders/health`, `/users/health`, `/payments/health`, `/inventory/health`
6. Verify load balancing page:
   - `http://localhost:8080/load-test` and `/orders/lbtest`
7. Verify failure simulation:
   - call `/inventory/simulate-failure`
   - then call `/payments/process`

## Nginx Routing
Path-based routes emulate AWS ALB behavior:
- `/orders/*` -> order-service
- `/users/*` -> user-service
- `/payments/*` -> payment-service
- `/inventory/*` -> inventory-service
- `/*` -> frontend

## AWS Deployment Artifacts

### ECS
- `deploy/ecs/task-definitions.json`
- `deploy/ecs/service-definitions.md`
- `deploy/ecs/complete-custom-vpc-guide.md`
  - task/service definition guidance
  - ALB design
  - target group design
  - full click-by-click deployment in custom VPC

### EKS
- `deploy/eks/namespace.yaml`
- `deploy/eks/deployment.yaml`
- `deploy/eks/service.yaml`
- `deploy/eks/ingress.yaml`
- `deploy/eks/hpa.yaml`
- `deploy/eks/complete-custom-vpc-guide.md`
  - full click-by-click deployment in custom VPC

## AWS Deployment Guide (Beginner Friendly)

For full spoon-fed deployment steps (starting from custom VPC creation until endpoint validation), use:

1. **ECS (Fargate) custom VPC guide**: `deploy/ecs/complete-custom-vpc-guide.md`
2. **EKS custom VPC guide**: `deploy/eks/complete-custom-vpc-guide.md`
