def main():
    print("Hello from sdk-deployment-test!")


if __name__ == "__main__":
    main()
bash-3.2$ cat python_gcp_Agent.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime,timezone
from strands import Agent
import os
from strands.models.gemini import GeminiModel

app = FastAPI(title="Strands Agent Server", version="1.0.0")

gemini_model = GeminiModel(
  client_args={
    "api_key": os.environ['GOOGLE_API_KEY'],
  },
  model_id="gemini-2.5-flash",
  params={"temperature": 0.7}
)
strands_agent = Agent(model=gemini_model)


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

