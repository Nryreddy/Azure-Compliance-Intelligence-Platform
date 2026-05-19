import uuid       
import logging    
from fastapi import FastAPI, HTTPException, BackgroundTasks
# HTTPException = handles errors with proper HTTP status codes

from pydantic import BaseModel  
#Pydantic = data validation library (ensures API requests have correct format)

from typing import List, Optional  
# Type hints for better code clarity and auto-completion

from dotenv import load_dotenv
load_dotenv(override=True)  

#INITIALIZE TELEMETRY
from backend.src.api.telemetry import setup_telemetry
setup_telemetry()  
# starts tracking all API activity

from backend.src.graph.workflow import app as compliance_graph


# CONFIGURE LOGGING
logging.basicConfig(level=logging.INFO)  

logger = logging.getLogger("api-server")  

# CREATE FASTAPI APPLICATION 
app = FastAPI(
    title="Azure AI Compliance API",
    description="API for auditing video content against brand compliance rules.",
    version="1.0.0"
)


# IN-MEMORY JOB STORE (For async status tracking)
# In production, use Redis or a Database
jobs = {}

#  DEFINE DATA MODELS (PYDANTIC) 

# --- REQUEST MODEL ---
class AuditRequest(BaseModel):
    """
    Defines the expected structure of incoming API requests.
    
    Pydantic validates that:
    - The request contains a 'video_url' field
    - The value is a string (not int, list, etc.)
    
    Example valid request:
    {
        "video_url": "https://youtu.be/abc123"
    }
    
    Example invalid request (raises 422 error):
    {
        "video_url": 12345  ← Not a string!
    }
    """
    video_url: str  # Required string field


# --- NESTED MODEL ---
class ComplianceIssue(BaseModel):
    """
    Defines the structure of a single compliance violation.
    
    Used inside AuditResponse to represent each violation found.
    """
    category: str      # Example: "Misleading Claims"
    severity: str      # Example: "CRITICAL"
    description: str   # Example: "Absolute guarantee detected at 00:32"


# --- RESPONSE MODEL ---
class AuditResponse(BaseModel):
    """
    Defines the structure of API responses.
    """
    session_id: str                           # Unique audit session ID
    video_id: str                             # Shortened video identifier
    status: str                               # PASS or FAIL
    final_report: str                         # LLM summary
    compliance_results: List[ComplianceIssue] # List of violations

class JobResponse(BaseModel):
    """
    Response returned immediately when an audit is accepted.
    """
    session_id: str
    message: str

def run_audit_background(session_id: str, initial_inputs: dict):
    """
    Background task to execute the compliance graph without blocking the API.
    """
    try:
        jobs[session_id]["status"] = "processing"
        final_state = compliance_graph.invoke(initial_inputs)
        
        jobs[session_id]["status"] = "completed"
        jobs[session_id]["result"] = AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "UNKNOWN"),
            final_report=final_state.get("final_report", "No report generated."),
            compliance_results=final_state.get("compliance_results", [])
        ).model_dump()
    except Exception as e:
        logger.error(f"Background Audit Failed for {session_id}: {str(e)}")
        jobs[session_id]["status"] = "failed"
        jobs[session_id]["error"] = str(e)

#DEFINE MAIN ENDPOINT
@app.post("/audit", response_model=JobResponse, status_code=202)

async def audit_video(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Main API endpoint that triggers the compliance audit workflow.
    
    Request Body:
    {
        "video_url": "https://youtu.be/abc123"
    }
    Response: AuditResponse object (defined above)
    
    Process:
    1. Generate unique session ID
    2. Prepare input for LangGraph workflow
    3. Invoke the graph (Indexer → Auditor)
    4. Return formatted results
    """
    
    #  GENERATE SESSION ID
    session_id = str(uuid.uuid4())
    
    video_id_short = f"vid_{session_id[:8]}" 
    # Easier to reference in logs/UI than full UUID
    
    #  LOG INCOMING REQUEST 
    logger.info(f"Received Audit Request: {request.video_url} (Session: {session_id})")

    initial_inputs = {
        "video_url": request.video_url,  # From the API request
        "video_id": video_id_short,      # Generated ID
        "compliance_results": [],        # Will be populated by Auditor
        "errors": []                     # Tracks any processing errors
    }

    try:
        #  STORE JOB AND START BACKGROUND TASK
        jobs[session_id] = {"status": "pending"}
        background_tasks.add_task(run_audit_background, session_id, initial_inputs)
        
        return JobResponse(
            session_id=session_id,
            message="Audit job accepted and running in background. Poll /audit/{session_id} for status."
        )

    except Exception as e:
        logger.error(f"Audit Failed to start: {str(e)}")
        
        raise HTTPException(
            status_code=500,  # 500 = Internal Server Error
            detail=f"Workflow Execution Failed to start: {str(e)}"
        )

@app.get("/audit/{session_id}")
async def get_audit_status(session_id: str):
    """
    Endpoint to check the real-time status of a background audit job.
    """
    job = jobs.get(session_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# HEALTH CHECK ENDPOINT
@app.get("/health")
# ↑ GET request at http://localhost:8000/health
def health_check():
    """
    Simple endpoint to verify the API is running.
    
    Used by:
    - Load balancers (to check if server is alive)
    - Monitoring systems (uptime checks)
    - Developers (quick test that server started)
    """
    return {"status": "healthy", "service": "Azure Compliance Intelligence Platform"}