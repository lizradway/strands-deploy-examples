# Python Deployment to Kubernetes

This guide covers deploying Python-based Strands agents to Kubernetes using Kind (Kubernetes in Docker) for local development.

## Prerequisites

- Python 3.10+
- [Docker](https://www.docker.com/) installed and running
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- AWS credentials with Bedrock access permissions

### Setup Kind Cluster

1. Create a Kind cluster:
```bash
kind create cluster --name <cluster-name>
```

2. Verify cluster is running:
```bash
kubectl get nodes
```

---

## Deploying to Kubernetes

This approach demonstrates how to deploy a custom agent using FastAPI and Docker to a local Kubernetes cluster.

**Requirements**

- **FastAPI Server**: Web server framework for handling requests
- **`/invocations` Endpoint**: POST endpoint for agent interactions
- **`/ping` Endpoint**: GET endpoint for health checks
- **Container Engine**: Docker for building images
- **Kubernetes Manifests**: Deployment and Service configurations
- **AWS Credentials**: Access key, secret key, and session token (for temporary credentials)

### Step 1: Configure AWS Credentials

1. Update the AWS credentials in `k8s-deployment.yaml`:
```yaml
env:
- name: AWS_ACCESS_KEY_ID
  value: "your-access-key"
- name: AWS_SECRET_ACCESS_KEY
  value: "your-secret-key"
- name: AWS_SESSION_TOKEN
  value: "your-session-token"  # Required for temporary credentials
- name: AWS_DEFAULT_REGION
  value: "us-east-1"
```

**Note**: If your access key starts with "ASIA", you're using temporary credentials and must include the session token.

### Step 2: Build and Load Docker Image

1. Build your Docker image:
```bash
docker build -t <image-name>:latest .
```

2. Load image into Kind cluster:
```bash
kind load docker-image <image-name>:latest --name <cluster-name>
```

### Step 3: Deploy to Kubernetes

1. Apply the Kubernetes manifests:
```bash
kubectl apply -f k8s-deployment.yaml
```

2. Verify deployment:
```bash
kubectl get pods
kubectl get services
```

**Important**: After updating AWS credentials in the YAML, you must restart the deployment:
```bash
kubectl rollout restart deployment <app-name>
```

### Step 4: Test Your Deployment

1. Port forward to access the service:
```bash
kubectl port-forward svc/<service-name> 8080:8080
```

2. Test the endpoints:
```bash
# Health check
curl http://localhost:8080/ping

# Test agent invocation
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello, how are you?"}}'
```

### Step 5: Making Changes

When you modify your code, redeploy with:

```bash
# Rebuild image
docker build -t <image-name>:latest .

# Load into cluster
kind load docker-image <image-name>:latest --name <cluster-name>

# Restart deployment
kubectl rollout restart deployment <app-name>
```


## Troubleshooting

- **Pod not starting**: Check logs with `kubectl logs <pod-name>`
- **Connection refused**: Verify app is listening on 0.0.0.0:8080
- **Image not found**: Ensure image is loaded with `kind load docker-image`
- **Dependencies missing**: Check `pyproject.toml` and rebuild image
- **"Unable to locate credentials"**: Verify AWS credentials are set and restart deployment
- **AWS credentials not found**: Check environment variables with `kubectl exec <pod-name> -- env | grep AWS`
- **Bedrock access denied**: Ensure your AWS role has `bedrock:InvokeModel` permissions

## Cleanup

Remove the Kind cluster when done:
```bash
kind delete cluster --name <cluster-name>
```
