from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Any, Optional
import uvicorn

from pyos.core.config import get_settings
from pyos.core.orchestrator import PyOSOrchestrator

app = FastAPI(
    title="PyOS-Agent API",
    description="Interface para controle do agente autônomo PyOS",
    version="0.1.0"
)

settings = get_settings()
orchestrator = PyOSOrchestrator(settings=settings)

class ObjectiveRequest(BaseModel):
    objective: str

class ObjectiveResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict[str, Any]] = None

@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online"
    }

@app.get("/config")
async def get_config():
    return settings.to_dict()

@app.post("/execute", response_model=ObjectiveResponse)
async def execute_objective(request: ObjectiveRequest):
    try:
        result = await orchestrator.execute_objective(request.objective)
        return ObjectiveResponse(
            success=result.get("success", False),
            message="Objetivo processado",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

if __name__ == "__main__":
    start_api()
