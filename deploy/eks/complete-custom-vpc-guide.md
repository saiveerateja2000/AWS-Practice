# EKS Deployment Guide (Custom VPC, Click-by-Click)

This guide gives exact AWS Console and CLI steps to deploy this app on **Amazon EKS** with a **custom VPC**.

---

## 1) Prerequisites

1. Log in to AWS Console.
2. Pick one AWS region and use it everywhere (example: `ap-south-1`).
3. Install locally:
   - AWS CLI v2
   - Docker
   - kubectl
   - eksctl
   - helm
4. Configure AWS credentials:
   ```bash
   aws configure
   ```
5. Confirm identity:
   ```bash
   aws sts get-caller-identity
   ```

---

## 2) Names and Network Values

Use these values consistently:

- VPC name: `traffic-vpc`
- VPC CIDR: `10.40.0.0/16`
- Public subnet A: `10.40.0.0/24`
- Public subnet B: `10.40.1.0/24`
- Private subnet A: `10.40.10.0/24`
- Private subnet B: `10.40.11.0/24`
- EKS cluster: `cloud-native-traffic-eks`
- Node group: `traffic-ng-private`
- Kubernetes namespace: `cloud-native-traffic`

---

## 3) Create Custom VPC (Console)

1. Open **VPC**.
2. Click **Create VPC**.
3. Select **VPC and more**.
4. Set:
   - Name: `traffic-vpc`
   - IPv4 CIDR: `10.40.0.0/16`
   - AZs: `2`
   - Public subnets: `2`
   - Private subnets: `2`
   - NAT gateways: `1 per AZ` (recommended) or `1` (cheaper)
5. Click **Create VPC**.

---

## 4) Tag Subnets for EKS and ALB Controller

Open **VPC > Subnets** and add tags.

### Public subnets (both)
Add:
- `kubernetes.io/role/elb` = `1`

### Private subnets (both)
Add:
- `kubernetes.io/role/internal-elb` = `1`

### All subnets used by this cluster
Add:
- `kubernetes.io/cluster/cloud-native-traffic-eks` = `shared`

---

## 5) Create ECR Repositories

In **ECR > Repositories**, create:

- `frontend`
- `order-service`
- `user-service`
- `payment-service`
- `inventory-service`

---

## 6) Build and Push Images

From repository root:

```bash
cd /tmp/workspace/saiveerateja2000/AWS-Practice
export AWS_REGION=ap-south-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

Build and push images:

```bash
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

## 7) Create EKS Cluster in Custom VPC

### Option A (recommended): using `eksctl`

1. Get private subnet IDs and security group details from VPC console.
2. Run:
   ```bash
   eksctl create cluster \
     --name cloud-native-traffic-eks \
     --region ap-south-1 \
     --version 1.30 \
     --vpc-private-subnets subnet-aaaa,subnet-bbbb \
     --vpc-public-subnets subnet-cccc,subnet-dddd \
     --nodegroup-name traffic-ng-private \
     --node-type t3.medium \
     --nodes 2 \
     --nodes-min 2 \
     --nodes-max 5 \
     --managed
   ```
3. Wait until cluster is active.

### Option B: Console

1. Open **EKS > Clusters > Create**.
2. Choose **Custom configuration**.
3. Cluster name: `cloud-native-traffic-eks`.
4. Kubernetes version: latest stable.
5. Cluster IAM role: create/select one with required EKS policies.
6. Networking:
   - VPC: `traffic-vpc`
   - Subnets: choose all 4 subnets
   - Endpoint access: public + private (default acceptable)
7. Create cluster.
8. Add managed node group:
   - Node group name: `traffic-ng-private`
   - Node IAM role with EKS worker permissions
   - Subnets: private subnets
   - Instance type: `t3.medium`
   - Desired size: `2`

---

## 8) Configure kubectl Access

```bash
aws eks update-kubeconfig --region ap-south-1 --name cloud-native-traffic-eks
kubectl get nodes
```

If nodes are `Ready`, continue.

---

## 9) Install AWS Load Balancer Controller

Follow AWS official steps for IAM OIDC provider and controller IAM policy, then install with Helm.

Minimum commands pattern:

```bash
eksctl utils associate-iam-oidc-provider --region ap-south-1 --cluster cloud-native-traffic-eks --approve
```

Then create IAM policy/service account and install chart from `eks/aws-load-balancer-controller`.

Verify:

```bash
kubectl -n kube-system get deployment aws-load-balancer-controller
```

---

## 10) Update Kubernetes Manifests with Your ECR URIs

Edit `/deploy/eks/deployment.yaml` and replace all:
- `<account>` with AWS account ID
- `<region>` with region

Then apply manifests:

```bash
cd /tmp/workspace/saiveerateja2000/AWS-Practice
kubectl apply -f deploy/eks/namespace.yaml
kubectl apply -f deploy/eks/deployment.yaml
kubectl apply -f deploy/eks/service.yaml
kubectl apply -f deploy/eks/ingress.yaml
kubectl apply -f deploy/eks/hpa.yaml
```

---

## 11) Validate Pods and Services

```bash
kubectl get pods -n cloud-native-traffic
kubectl get svc -n cloud-native-traffic
kubectl get ingress -n cloud-native-traffic
```

Wait for ingress `ADDRESS` (ALB DNS) to appear.

---

## 12) Validate Application Endpoints

Open `http://<alb-dns-name>` and test:

- `/`
- `/orders/details`
- `/payments/process`
- `/orders/health`
- `/users/health`
- `/payments/health`
- `/inventory/health`

---

## 13) Enable Metrics Server (for HPA)

If HPA shows no metrics, install metrics-server:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Check:

```bash
kubectl top pods -n cloud-native-traffic
kubectl get hpa -n cloud-native-traffic
```

---

## 14) Common Fixes

- **Ingress created but no ALB DNS**: confirm AWS Load Balancer Controller is running and subnet tags are correct.
- **ImagePullBackOff**: confirm ECR URI, image tag, and node role permissions.
- **Pods pending**: check node group size and subnet IP availability.
- **No downstream service response**: verify service names/ports in `service.yaml`.

---

## 15) Cleanup (Avoid Cost)

1. Delete k8s resources:
   ```bash
   kubectl delete -f deploy/eks/hpa.yaml
   kubectl delete -f deploy/eks/ingress.yaml
   kubectl delete -f deploy/eks/service.yaml
   kubectl delete -f deploy/eks/deployment.yaml
   kubectl delete -f deploy/eks/namespace.yaml
   ```
2. Delete EKS cluster and node group.
3. Delete ALB created by ingress controller.
4. Delete NAT gateways.
5. Delete VPC.
6. Delete ECR images/repositories (optional).
