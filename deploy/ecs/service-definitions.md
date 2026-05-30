# ECS Service Definitions

- ECS Cluster: `cloud-native-traffic-cluster`
- ECS Service: `cloud-native-traffic-service`
- Launch Type: Fargate
- Desired tasks: start with 2
- Auto Scaling: target CPU 60%, memory 70%

## ALB Design
- Internet-facing ALB in public subnets
- Listener: HTTP 80 (and HTTPS 443 in production)
- Rule paths:
  - `/orders/*` -> order target group
  - `/users/*` -> user target group
  - `/payments/*` -> payment target group
  - `/inventory/*` -> inventory target group
  - `/*` -> frontend target group

## Target Group Design
- Target type: IP
- Protocol: HTTP
- Port: 5000 for app services, 80 for nginx if fronting all routes
- Health check path: `/health`
