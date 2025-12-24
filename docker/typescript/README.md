# TypeScript Deployment to Docker

This guide covers deploying TypeScript-based Strands agents using Docker for local and cloud development.

## Prerequisites

- Node.js 20+
- [Docker](https://www.docker.com/) installed and running
- Model provider credentials

---

## Deploying with Docker

### Quick Start Setup

Configure Model Provider Credentials:
```bash
# OpenAI (used in this example)
export OPENAI_API_KEY='<your-api-key>'
```

**Note**: This example uses OpenAI, but any supported model provider can be configured. See the [Strands model credential documentation](https://strandsagents.com/latest/documentation/docs/user-guide/quickstart/typescript/#configuring-credentials) for other model providers.

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

// Note: Any supported model provider can be configured
const model = new OpenAIModel({
  apiKey: process.env.OPENAI_API_KEY || '<your-api-key>',
  modelId: 'gpt-4o',
})

const agent = new Agent({ model })

const app = express()

// Middleware to parse JSON
app.use(express.json())

// Health check endpoint
app.get('/ping', (_, res) =>
  res.json({
    status: 'healthy',
  })
)

// Agent invocation endpoint
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
# Use Node 20+
FROM node:20

WORKDIR /app

# Copy source code
COPY . ./

# Install dependencies
RUN npm install

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
```

### Step 1: Build Docker Image

Build your Docker image:
```bash
docker build -t <image-name>:latest .
```

### Step 2: Run Docker Container

Run the container with OpenAI credentials:
```bash
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  <image-name>:latest
```

### Step 3: Test Your Deployment

Test the endpoints:
```bash
# Health check
curl http://localhost:8080/ping

# Test agent invocation
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello, how are you?"}}'
```

### Step 4: Making Changes

When you modify your code, rebuild and run:

```bash
# Rebuild image
docker build -t <image-name>:latest .

# Stop existing container (if running)
docker stop $(docker ps -q --filter ancestor=<image-name>:latest)

# Run new container
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  <image-name>:latest
```

## Troubleshooting

- **Container not starting**: Check logs with `docker logs <container-id>`
- **Connection refused**: Verify app is listening on 0.0.0.0:8080
- **Image build fails**: Check `package.json` and dependencies
- **TypeScript compilation errors**: Check `tsconfig.json` and run `npm run build` locally
- **"Unable to locate credentials"**: Verify model provider credentials environment variables are set
- **Port already in use**: Use different port mapping `-p 8081:8080`

## Cleanup

Stop and remove containers:
```bash
# Stop all containers using your image
docker stop $(docker ps -q --filter ancestor=<image-name>:latest)

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune
```

## Optional: Deploy to Cloud Container Service

Once your application works locally with Docker, you can deploy it to any cloud-hosted container service:

### Steps for Cloud Deployment

1. **Push your image to a container registry**:
```bash
# Tag and push to your registry (Docker Hub, ECR, GCR, etc.)
docker tag <image-name>:latest <registry-url>/<image-name>:latest
docker push <registry-url>/<image-name>:latest
```

2. **Deploy using your cloud provider's container service**:
   - Update image URL to use your registry: `<registry-url>/<image-name>:latest`
   - Configure environment variables for model credentials
   - Deploy the container with port 8080 exposed

**Note**: Your cloud service needs permissions to:
- Pull images from your container registry
- Access your chosen model provider credentials

## Optional: Docker Compose

For easier management, create a `docker-compose.yml`:

```yaml
# Example for OpenAI
version: '3.8'
services:
  <app-name>:
    build: .
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=<your-api-key>
```

Run with Docker Compose:
```bash
# Start services
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop services
docker-compose down
```
