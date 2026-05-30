# ECS Fargate Deployment Guide (Custom VPC, Click-by-Click)

This guide gives exact AWS Console and CLI steps to deploy this app on **Amazon ECS Fargate** with a **custom VPC**.

---

## 1) Prerequisites

1. Log in to AWS Console.
2. Select a region (example: `ap-south-1`) and use the same region for all steps.
3. Install locally:
   - AWS CLI v2
   - Docker
4. Configure CLI credentials:
   ```bash
   aws configure
   ```
5. Confirm AWS account ID:
   ```bash
   aws sts get-caller-identity
   ```

---

## 2) Naming and Values (Use These Everywhere)

Set these values in your notes before clicking anything:

- VPC name: `traffic-vpc`
- VPC CIDR: `10.40.0.0/16`
- Public subnet A: `10.40.0.0/24`
- Public subnet B: `10.40.1.0/24`
- Private subnet A: `10.40.10.0/24`
- Private subnet B: `10.40.11.0/24`
- ECS cluster: `cloud-native-traffic-ecs`
- ECS service: `cloud-native-traffic-service`
- Task family: `cloud-native-traffic-platform`

---

## 3) Create Custom VPC (Console)

1. Open **VPC** service.
2. Click **Create VPC**.
3. Choose **VPC and more**.
4. Enter:
   - Name tag auto-generation: `traffic-vpc`
   - IPv4 CIDR block: `10.40.0.0/16`
   - Number of Availability Zones: `2`
   - Number of public subnets: `2`
   - Number of private subnets: `2`
   - NAT gateways: `1 per AZ` (recommended) or `1` (cheaper)
   - VPC endpoints: `None` (optional)
5. Click **Create VPC**.
6. Wait until status is complete.

### Verify VPC Objects

Go to VPC pages and confirm:
- 1 Internet Gateway attached
- Public route table has route `0.0.0.0/0 -> igw-*`
- Private route table has route `0.0.0.0/0 -> nat-*`

---

## 4) Create Security Groups

Go to **VPC > Security Groups**.

### A) ALB Security Group

1. Click **Create security group**.
2. Name: `traffic-ecs-alb-sg`.
3. VPC: `traffic-vpc`.
4. Inbound rules:
   - HTTP, TCP 80, Source `0.0.0.0/0`
5. Outbound: allow all.
6. Create.

### B) ECS Task Security Group

1. Click **Create security group**.
2. Name: `traffic-ecs-task-sg`.
3. VPC: `traffic-vpc`.
4. Inbound rules:
   - Custom TCP 80, Source `traffic-ecs-alb-sg`
5. Outbound: allow all.
6. Create.

---

## 5) Create ECR Repositories

Go to **ECR > Repositories > Create repository** and create these 6 repos:

- `nginx`
- `frontend`
- `order-service`
- `user-service`
- `payment-service`
- `inventory-service`

---

## 6) Build and Push Images

Run from repository root:

```bash
cd /tmp/workspace/saiveerateja2000/AWS-Practice
export AWS_REGION=ap-south-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

Build and push each image:

```bash
docker build -t nginx:v1.0.0 ./nginx
docker tag nginx:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nginx:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nginx:v1.0.0

docker build -t frontend:v1.0.0 ./frontend
docker tag frontend:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/frontend:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/frontend:v1.0.0

docker build -t order-service:v1.0.0 ./services/order-service
docker tag order-service:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/order-service:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/order-service:v1.0.0

docker build -t user-service:v1.0.0 ./services/user-service
docker tag user-service:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/user-service:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/user-service:v1.0.0

docker build -t payment-service:v1.0.0 ./services/payment-service
docker tag payment-service:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/payment-service:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/payment-service:v1.0.0

docker build -t inventory-service:v1.0.0 ./services/inventory-service
docker tag inventory-service:v1.0.0 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/inventory-service:v1.0.0
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/inventory-service:v1.0.0
```

---

## 7) Create IAM Roles

### A) ECS Task Execution Role

1. Open **IAM > Roles > Create role**.
2. Trusted entity: **AWS service**.
3. Use case: **Elastic Container Service Task**.
4. Attach policy: `AmazonECSTaskExecutionRolePolicy`.
5. Role name: `ecsTaskExecutionRole`.
6. Create role.

### B) Task Role

1. Create another role with trusted entity **ECS Task**.
2. Name: `cloud-native-traffic-task-role`.
3. Attach minimal required permissions (start with CloudWatch logs read/write if needed).
4. Create role.

---

## 8) Create CloudWatch Log Group

1. Open **CloudWatch > Log groups**.
2. Click **Create log group**.
3. Name: `/ecs/cloud-native-traffic`.
4. Create.

---

## 9) Register Task Definition

1. Open **ECS > Task definitions > Create new task definition**.
2. Launch type compatibility: **Fargate**.
3. Name: `cloud-native-traffic-platform`.
4. CPU: `1 vCPU`.
5. Memory: `2 GB`.
6. Execution role: `ecsTaskExecutionRole`.
7. Task role: `cloud-native-traffic-task-role`.
8. Add 6 containers exactly as in `/deploy/ecs/task-definitions.json`.
9. For `nginx` expose container port `80`; all other containers use `5000`.
10. Add awslogs logging for each container:
    - Log group: `/ecs/cloud-native-traffic`
    - Region: your region
    - Stream prefix: container name
11. Create task definition.

> Tip: Replace `<account>` and `<region>` placeholders from `task-definitions.json` before using values.

---

## 10) Create ECS Cluster

1. Open **ECS > Clusters > Create cluster**.
2. Cluster name: `cloud-native-traffic-ecs`.
3. Infrastructure: **AWS Fargate (serverless)**.
4. Create.

---

## 11) Create Application Load Balancer

1. Open **EC2 > Load Balancers > Create**.
2. Type: **Application Load Balancer**.
3. Name: `traffic-ecs-alb`.
4. Scheme: **Internet-facing**.
5. IP type: IPv4.
6. Network mapping: choose `traffic-vpc` and **both public subnets**.
7. Security group: `traffic-ecs-alb-sg`.
8. Listener: HTTP 80.
9. Create.

---

## 12) Create Target Group (for nginx)

1. Open **EC2 > Target Groups > Create target group**.
2. Target type: **IP**.
3. Name: `traffic-ecs-nginx-tg`.
4. Protocol: HTTP.
5. Port: `80`.
6. VPC: `traffic-vpc`.
7. Health check path: `/`.
8. Create.

Attach target group to ALB listener default action.

---

## 13) Create ECS Service

1. Open **ECS > Clusters > cloud-native-traffic-ecs**.
2. Click **Create service**.
3. Launch type: **Fargate**.
4. Task definition family: `cloud-native-traffic-platform`.
5. Service name: `cloud-native-traffic-service`.
6. Desired tasks: `2`.
7. Networking:
   - VPC: `traffic-vpc`
   - Subnets: both private subnets
   - Security group: `traffic-ecs-task-sg`
   - Auto-assign public IP: `DISABLED`
8. Load balancing:
   - Type: **Application Load Balancer**
   - Existing ALB: `traffic-ecs-alb`
   - Target group: `traffic-ecs-nginx-tg`
   - Container: `nginx:80`
9. Create service.

---

## 14) Verify Deployment

1. Wait until ECS tasks are `RUNNING`.
2. Open ALB DNS name in browser.
3. Validate:
   - `/` dashboard loads
   - `/orders/details`
   - `/payments/process`
   - `/orders/health`, `/users/health`, `/payments/health`, `/inventory/health`
4. Check logs in CloudWatch log group `/ecs/cloud-native-traffic`.

---

## 15) Common Fixes

- **Tasks not starting**: check ECS service events for IAM/image pull/log permission errors.
- **ALB returns 503**: verify target group health checks and task SG inbound rule from ALB SG.
- **Image pull fail**: verify ECR image URI/tag and task execution role permissions.
- **No internet from private tasks**: verify NAT gateway route in private route table.

---

## 16) Cleanup (Avoid Extra Cost)

Delete in this order:
1. ECS service
2. ECS cluster
3. ALB + target group
4. NAT gateways
5. VPC
6. ECR images/repositories (optional)
7. CloudWatch log group (optional)
