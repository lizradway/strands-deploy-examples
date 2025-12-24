# Python Deployment to Docker

This guide covers deploying Python-based Strands agents using Docker for for local and cloud development.

## Prerequisites

- Python 3.10+
- [Docker](https://www.docker.com/) installed and running
- AWS credentials with Bedrock access permissions (or model provider of your choice)

---

## Deploying with Docker

### Quick Start Setup

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Configure AWS Credentials:
```bash
export AWS_ACCESS_KEY_ID='<your-access-key>'
export AWS_SECRET_ACCESS_KEY='<your-secret-key>'
export AWS_SESSION_TOKEN='<your-session-token>'  # Required for temporary credentials
export AWS_DEFAULT_REGION='us-east-1'
```

Create Project:
```bash
mkdir <app-name> && cd <app-name>
uv init --python 3.11
uv add fastapi uvicorn[standard] pydantic strands-agents
```

Project Structure:
```
<app-name>/
├── agent.py                # FastAPI application
├── Dockerfile              # Container configuration
├── pyproject.toml          # Created by uv init
└── uv.lock                 # Created automatically by uv
```

Create agent.py:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timezone
import os
from strands import Agent
from strands.models.bedrock import BedrockModel

app = FastAPI(title="Strands Agent Server", version="1.0.0")

bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    params={"temperature": 0.7, "max_tokens": 1000}
)

strands_agent = Agent(model=bedrock_model)

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        result = strands_agent(user_message)
        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "strands-agent",
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

Create Dockerfile:
```dockerfile
FROM python:3.11

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY agent.py ./

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 1: Build Docker Image

Build your Docker image:
```bash
docker build -t <image-name>:latest .
```

### Step 2: Run Docker Container

Run the container with AWS credentials:
```bash
docker run -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  -e AWS_DEFAULT_REGION="us-east-1" \
  <image-name>:latest
```

**Note**: If your access key starts with "ASIA", you're using temporary credentials and must include the session token.

### Step 3: Test Your Deployment

Test the endpoints:
```bash
# Health check
curl http://localhost:8080/ping

# Test agent invocation
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "What is artificial intelligence?"}}'
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
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  -e AWS_DEFAULT_REGION="us-east-1" \
  <image-name>:latest
```

## Troubleshooting

- **Container not starting**: Check logs with `docker logs <container-id>`
- **Connection refused**: Verify app is listening on 0.0.0.0:8080
- **Image build fails**: Check `pyproject.toml` and dependencies
- **"Unable to locate credentials"**: Verify AWS environment variables are set
- **Bedrock access denied**: Ensure your AWS role has `bedrock:InvokeModel` permissions
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
   - Configure environment variables for AWS credentials
   - Deploy the container with port 8080 exposed

**Note**: Your cloud service needs permissions to:
- Pull images from your container registry
- Access your chosen model provider credentials

## Optional: Docker Compose

For easier management, create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  <app-name>:
    build: .
    ports:
      - "8080:8080"
    environment:
      - AWS_ACCESS_KEY_ID=<your-access-key>
      - AWS_SECRET_ACCESS_KEY=<your-secret-key>
      - AWS_SESSION_TOKEN=<your-session-token>
      - AWS_DEFAULT_REGION=us-east-1
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
