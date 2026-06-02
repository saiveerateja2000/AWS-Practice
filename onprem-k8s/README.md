# On-Prem Kubernetes Guide

This is the exact copy-paste runbook we used for the on-prem setup.

## 1) Apply the app manifests

```bash
kubectl apply -f onprem-k8s/namespace.yaml
kubectl apply -f onprem-k8s/deployment.yaml
kubectl apply -f onprem-k8s/service.yaml
kubectl apply -f onprem-k8s/ingress.yaml
kubectl apply -f onprem-k8s/hpa.yaml
```

## 2) Verify the workloads

```bash
kubectl -n cloud-native-traffic get pods,deploy,svc,ingress,hpa
kubectl -n ingress-nginx get pods,svc
```

## 3) Make ingress-nginx reachable

We used `ingress-nginx` and then exposed its controller with `NodePort`.

If the controller Service is still `LoadBalancer` with `<pending>` EXTERNAL-IP, patch it:

```bash
kubectl -n ingress-nginx patch svc ingress-nginx-controller -p '{"spec":{"type":"NodePort"}}'
kubectl -n ingress-nginx get svc ingress-nginx-controller -o wide
```

The NodePort we used was `31019`.

## 4) Access the application

Get a node IP:

```bash
kubectl get nodes -o wide
```

Open the app through the ingress controller NodePort:

```bash
curl http://<NODE_IP>:31019/
curl http://<NODE_IP>:31019/orders/details
curl http://<NODE_IP>:31019/payments/process
```

If you only want a quick local test, port-forward the frontend:

```bash
kubectl -n cloud-native-traffic port-forward svc/frontend 8080:5000
```

Then open:

```bash
http://localhost:8080
```

## 5) Why the Ingress ADDRESS was empty

The `Ingress` resource only defines routing rules. It does not create an external endpoint by itself.

In our cluster:

- `ingress-nginx` was installed
- the controller Service was exposed with `NodePort`
- the app was reachable through `http://<NODE_IP>:31019`

We did not use MetalLB.

## 6) Redeploy on another on-prem cluster

Use the same flow:

```bash
kubectl apply -f onprem-k8s/namespace.yaml
kubectl apply -f onprem-k8s/deployment.yaml
kubectl apply -f onprem-k8s/service.yaml
kubectl apply -f onprem-k8s/ingress.yaml
kubectl apply -f onprem-k8s/hpa.yaml
kubectl -n ingress-nginx patch svc ingress-nginx-controller -p '{"spec":{"type":"NodePort"}}'
kubectl get nodes -o wide
kubectl -n cloud-native-traffic get pods,svc,ingress,hpa
```

If you want the same NodePort on another cluster, set `nodePort` explicitly in the controller Service. If you do not set it, Kubernetes may assign a different free port.

## 7) Clean up

```bash
kubectl delete -f onprem-k8s/
kubectl -n ingress-nginx delete svc ingress-nginx-controller
```