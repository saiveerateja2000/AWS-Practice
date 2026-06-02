#!/usr/bin/env bash

set -euo pipefail

K8S_MINOR_VERSION="${K8S_MINOR_VERSION:-v1.30}"
CRI_SOCKET="unix:///var/run/cri-dockerd.sock"

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

echo "Installing prerequisites..."
apt-get update
apt-get install -y ca-certificates curl gnupg

echo "Configuring kernel settings..."
cat >/etc/modules-load.d/kubernetes.conf <<'EOF'
overlay
br_netfilter
EOF
modprobe overlay
modprobe br_netfilter

cat >/etc/sysctl.d/kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system >/dev/null
swapoff -a || true
sed -i.bak '/\sswap\s/s/^/#/' /etc/fstab || true

echo "Installing Docker..."
apt-get install -y docker.io
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<'EOF'
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "storage-driver": "overlay2"
}
EOF
systemctl enable --now docker

echo "Installing cri-dockerd..."
curl -fsSL -o /tmp/cri-dockerd.deb "https://github.com/Mirantis/cri-dockerd/releases/download/v0.4.3/cri-dockerd_0.4.3.3-0.ubuntu-jammy_amd64.deb"
apt-get install -y /tmp/cri-dockerd.deb
systemctl enable --now cri-docker.socket || true

echo "Installing Kubernetes packages..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://pkgs.k8s.io/core:/stable:/${K8S_MINOR_VERSION}/deb/Release.key" | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
chmod a+r /etc/apt/keyrings/kubernetes-apt-keyring.gpg
cat >/etc/apt/sources.list.d/kubernetes.list <<EOF
deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${K8S_MINOR_VERSION}/deb/ /
EOF
apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

echo "Pointing kubelet to Docker runtime..."
mkdir -p /etc/default
cat >/etc/default/kubelet <<EOF
KUBELET_EXTRA_ARGS=--container-runtime-endpoint=${CRI_SOCKET}
EOF
systemctl enable kubelet

echo "Next step: run this on the control plane node:"
echo "kubeadm init --cri-socket=${CRI_SOCKET} --pod-network-cidr=10.244.0.0/16"
echo "After that, run:"
echo 'mkdir -p $HOME/.kube'
echo 'cp -i /etc/kubernetes/admin.conf $HOME/.kube/config'
echo 'kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml'
echo 'Then use the kubeadm join command on the worker nodes.'