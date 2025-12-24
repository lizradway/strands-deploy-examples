# TypeScript Deployment to Kubernetes

This guide covers deploying TypeScript-based Strands agents to Kubernetes using Kind (Kubernetes in Docker) for local development.

## Prerequisites

- Node.js 20+
- [Docker](https://www.docker.com/) installed and running
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- AWS credentials with Bedrock access permissions (or alternative model provider credentials of your choice)

### Setup Kind Cluster

1. Create a Kind cluster:
```bash
kind create cluster --name <cluster-name>
```

2. Verify cluster is running:
```bash
kubectl get nodes
```

### Quick Start Setup

Configure AWS Credentials for local Bedrock usage:
```bash
export AWS_ACCESS_KEY_ID='<your-access-key>'
export AWS_SECRET_ACCESS_KEY='<your-secret-key>'
export AWS_SESSION_TOKEN='<your-session-token>'  # Required for temporary credentials
export AWS_DEFAULT_REGION='us-east-1'
```

Create Project:
```bash
mkdir <app-name> && cd <app-name>
npm init -y
npm install @strands-agents/sdk express @types/express typescript ts-node
npm install -D @types/node
```

Project Structure:
```
<app-name>/
├── index.ts                # Express application
├── Dockerfile              # Container configuration
├── k8s-deployment.yaml     # Kubernetes manifests
├── package.json            # Created by npm init
├── tsconfig.json           # TypeScript configuration
└── package-lock.json       # Created automatically by npm
```

Create tsconfig.json:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

Update package.json scripts:
```json
{
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node index.ts"
  }
}
```

Create index.ts:
```typescript
import { Agent } from '@strands-agents/sdk'
import express, { type Request, type Response } from 'express'

const PORT = Number(process.env.PORT) || 8080

// Configure the agent with default Bedrock model
const agent = new Agent()

const app = express()

// Middleware to parse JSON
app.use(express.json())

// Health check endpoint (REQUIRED)
app.get('/ping', (_, res) =>
  res.json({
    status: 'healthy',
  })
)

// Agent invocation endpoint (REQUIRED)
app.post('/invocations', async (req: Request, res: Response) => {
  try {
    const { input } = req.body
    const prompt = input?.prompt || ''
    
    if (!prompt) {
      return res.status(400).json({
        detail: 'No prompt found in input. Please provide a "prompt" key in the input.'
      })
    }

    // Invoke the agent
    const result = await agent.invoke(prompt)
    
    const response = {
      message: result,
      timestamp: new Date().toISOString(),
      model: 'strands-agent',
    }

    return res.json({ output: response })
  } catch (err) {
    console.error('Error processing request:', err)
    return res.status(500).json({ 
      detail: `Agent processing failed: ${err instanceof Error ? err.message : 'Unknown error'}` 
    })
  }
})

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Strands Agent Server listening on port ${PORT}`)
  console.log(`📍 Endpoints:`)
  console.log(`   POST http://0.0.0.0:${PORT}/invocations`)
  console.log(`   GET  http://0.0.0.0:${PORT}/ping`)
})
```

Create Dockerfile:
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
```

Create k8s-deployment.yaml:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app-name>
spec:
  replicas: 1
  selector:
    matchLabels:
      app: <app-name>
  template:
    metadata:
      labels:
        app: <app-name>
    spec:
      containers:
      - name: <app-name>
        image: <image-name>:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        env:
        - name: AWS_ACCESS_KEY_ID
          value: "<your-access-key>"
        - name: AWS_SECRET_ACCESS_KEY
          value: "<your-secret-key>"
        - name: AWS_SESSION_TOKEN
          value: "<your-session-token>"
        - name: AWS_DEFAULT_REGION
          value: "us-east-1"
---
apiVersion: v1
kind: Service
metadata:
  name: <service-name>
spec:
  selector:
    app: <app-name>
  ports:
  - port: 8080
    targetPort: 8080
  type: NodePort
```

---

## Deploying to Kubernetes

### Step 1: Build and Load Docker Image

1. Build your Docker image:
```bash
docker build -t <image-name>:latest .
```

2. Load image into Kind cluster:
```bash
kind load docker-image <image-name>:latest --name <cluster-name>
```

### Step 2: Deploy to Kubernetes

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

### Step 3: Test Your Deployment

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

### Step 4: Making Changes

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
- **Dependencies missing**: Check `package.json` and rebuild image
- **"Unable to locate credentials"**: Verify AWS credentials are set and restart deployment
- **AWS credentials not found**: Check environment variables with `kubectl exec <pod-name> -- env | grep AWS`
- **Bedrock access denied**: Ensure your AWS role has `bedrock:InvokeModel` permissions
- **TypeScript compilation errors**: Check `tsconfig.json` and run `npm run build` locally

## Cleanup

Remove the Kind cluster when done:
```bash
kind delete cluster --name <cluster-name>
```

## Optional: Deploy to Cloud Kubernetes Cluster

Once your application works locally with Kind, you can deploy it to any cloud-hosted Kubernetes cluster:


### Steps for Cloud Deployment

1. **Push your image to a container registry**:
```bash
# Tag and push to your registry (Docker Hub, ECR, GCR, etc.)
docker tag <image-name>:latest <registry-url>/<image-name>:latest
docker push <registry-url>/<image-name>:latest
```

2. **Update the deployment configuration in `k8s-deployment.yaml`**:

   **Change the image pull policy:**
   ```yaml
   # Current (local development): Uses local cached images
   imagePullPolicy: Never
   
   # Change to (cloud deployment): Pulls image from registry
   imagePullPolicy: Always
   ```

   **Update the image URL:**
   ```yaml
   # Current (local development):
   image: <image-name>:latest
   
   # Change to (cloud deployment):
   image: <registry-url>/<image-name>:latest
   ```

   **Update the service type for external access:**
   ```yaml
   # Current (local development):
   type: NodePort
   
   # Change to (cloud deployment):
   type: LoadBalancer
   ```
   This gives your service a public IP address that users can access directly, instead of requiring port-forwarding or node IP addresses.

3. **Apply to your cloud cluster**:
```bash
# Connect to your cloud cluster (varies by provider)
kubectl config use-context <cloud-context>

# Deploy your application
kubectl apply -f k8s-deployment.yaml
```

**Note**: Your cloud cluster needs permissions to:
- Pull images from your container registry
- Access your chosen model provider credentials
