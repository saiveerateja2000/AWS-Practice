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
│   │   └── service_base.py
│   ├── user-service/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── service_base.py
│   ├── payment-service/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── service_base.py
│   └── inventory-service/
│       ├── app.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── service_base.py
└── deploy/
    ├── ecs/
    │   ├── service-definitions.md
│   │   └── task-definitions.json
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
- `order-service` -> `user-service` via `/orders/details`
- `payment-service` -> `inventory-service` via `/payments/process`

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
   - `http://localhost:8080/orders/orders/details`
   - `http://localhost:8080/payments/payments/process`
3. Verify request tracing: check `X-Request-ID` response header and downstream payloads
4. Verify logging: inspect JSON logs from service containers
5. Verify health checks:
   - `/orders/health`, `/users/health`, `/payments/health`, `/inventory/health`
6. Verify load balancing page:
   - `http://localhost:8080/load-test` and `/orders/lbtest`
7. Verify failure simulation:
   - call `/inventory/simulate-failure`
   - then call `/payments/payments/process`

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
  - task/service definition guidance
  - ALB design
  - target group design

### EKS
- `deploy/eks/namespace.yaml`
- `deploy/eks/deployment.yaml`
- `deploy/eks/service.yaml`
- `deploy/eks/ingress.yaml`
- `deploy/eks/hpa.yaml`

## AWS Deployment Guide (Beginner Friendly)

1. Create ECR repositories for each service and image.
2. Build docker images locally (`docker build`).
3. Authenticate Docker to ECR and push images.
4. Create IAM execution/task roles (ECS) and worker/node roles (EKS).
5. Configure security groups for ALB, ECS tasks, and EKS nodes.
6. Design a VPC with CIDR sized for growth.
7. Create public subnets across at least 2 AZs.
8. Create private subnets across at least 2 AZs.
9. Create NAT Gateway in public subnet for private egress.
10. Attach and configure Internet Gateway.
11. Configure route tables for public/private subnet traffic.
12. Create ECS cluster with Fargate capacity.
13. Create ECS service using task definition and private subnets.
14. Configure ECS ALB listener rules for route-based traffic.
15. Create EKS cluster (managed control plane).
16. Create managed node groups.
17. Install AWS Load Balancer Controller in EKS.
18. Apply Kubernetes manifests (`namespace`, `deployments`, `services`).
19. Apply ingress manifest and verify ALB creation.
20. Configure autoscaling with HPA and metrics server.
21. Send container logs to CloudWatch (ECS and EKS).
22. Validate endpoints, tracing headers, and failure simulation behavior.

