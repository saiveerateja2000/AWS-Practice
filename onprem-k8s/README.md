# On-Prem Routing Concept

This folder models the on-prem Kubernetes version of the stack.

There are two common ways to route requests:

1. Path-based ingress
   - Kubernetes Ingress matches paths like `/orders` and `/users`
   - Each path goes directly to the matching backend Service
   - The routing rules live in the cluster ingress config

2. Nginx proxy in the app layer
   - A dedicated `nginx` pod receives traffic first
   - Nginx reads `nginx.conf` and forwards requests to the app Services
   - Path rules are stored in the Nginx config instead of the Ingress resource

For production-style Kubernetes, the on-prem setup uses path-based Ingress to route traffic directly to the frontend and backend Services, while the cluster ingress controller handles the external entry point.

Why this matters:

- The frontend pod still exists as its own Deployment and Service.
- The frontend and backend pods are real workloads managed by Deployments.
- The app manifests do not need to deploy an extra Nginx router pod.
- If you want a Docker Compose-style setup, that routing lives in the app-side Nginx container instead.

In short: production on-prem Kubernetes usually keeps routing in Ingress and uses the application pods only for business logic.