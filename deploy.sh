set -e

# Get Infrastructure Details
WORKER_NAMES=$(gcloud compute instances list --filter="tags.items=k8s-worker" --format="value(name)")
ALL_NODES="k8s-master $WORKER_NAMES"

# Initialize Master Node
gcloud compute ssh k8s-master --zone=us-central1-a --command "sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --ignore-preflight-errors=NumCPU"

# Configure Kubectl on Master
gcloud compute ssh k8s-master --zone=us-central1-a --command "mkdir -p \$HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf \$HOME/.kube/config && sudo chown \$(id -u):\$(id -g) \$HOME/.kube/config"

# Install Flannel CNI
gcloud compute ssh k8s-master --zone=us-central1-a --command "kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml"

# Get Join Command
JOIN_CMD=$(gcloud compute ssh k8s-master --zone=us-central1-a --command "sudo kubeadm token create --print-join-command")

# Join Worker Nodes
for WORKER in $WORKER_NAMES; do
    echo "--- Joining Worker: $WORKER ---"
    gcloud compute ssh $WORKER --zone=us-central1-a --command "sudo $JOIN_CMD"
done

# Copy Files From Bucket
gcloud compute ssh k8s-master --zone=us-central1-a --command "mkdir -p fire-models && mkdir -p k8s && \
    gcloud storage cp gs://wildfire-detection/requirements.txt . && \
    gcloud storage cp gs://wildfire-detection/main.py . && \
    gcloud storage cp gs://wildfire-detection/Dockerfile . && \
    gcloud storage cp -r gs://wildfire-detection/fire-models/* fire-models/ && \
    gcloud storage cp -r gs://wildfire-detection/k8s/* k8s/"

# Build and Import Image on Master
echo "--- Building and Importing Image on k8s-master ---"
gcloud compute ssh k8s-master --zone=us-central1-a --command "
    sudo docker build -t wildfire-app . && \
    sudo docker save wildfire-app | sudo ctr -n k8s.io images import -
"

# Distribute Image to Worker Nodes
for WORKER in $WORKER_NAMES; do
    echo "--- Distributing Image to $WORKER ---"
    gcloud compute ssh k8s-master --zone=us-central1-a --command "sudo docker save wildfire-app" | \
    gcloud compute ssh $WORKER --zone=us-central1-a --command "sudo ctr -n k8s.io images import -"
done

# Deploy Application
gcloud compute ssh k8s-master --zone=us-central1-a --command "kubectl apply -f k8s/namespace.yaml && kubectl apply -f k8s/deployment.yaml && kubectl apply -f k8s/service.yaml"

echo "Access the app at: http://<WORKER_EXTERNAL_IP>:30080"