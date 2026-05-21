import os
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

from fastapi.middleware.cors import CORSMiddleware

# CREATE FASTAPI APPLICATION 
app = FastAPI(
    title="Azure AI Compliance API",
    description="API for auditing video content against brand compliance rules.",
    version="1.0.0"
)

# ADD CORS MIDDLEWARE
# Origins are driven by the ALLOWED_ORIGINS environment variable (comma-separated).
# Defaults to the local Vite dev server. Set this to your deployed frontend URL in production.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from backend.src.services.database import db_service

# IN-MEMORY JOB STORE REMOVED. Using Cosmos DB.

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
    video_name: Optional[str] = None # Optional user-defined name


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
    video_id = initial_inputs.get("video_id")
    video_url = initial_inputs.get("video_url")
    try:
        db_service.create_or_update_audit(session_id, video_url, video_id, status="processing")
        final_state = compliance_graph.invoke(initial_inputs)
        
        result_payload = AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "UNKNOWN"),
            final_report=final_state.get("final_report", "No report generated."),
            compliance_results=final_state.get("compliance_results", [])
        ).model_dump()
        
        db_service.create_or_update_audit(session_id, video_url, video_id, status="completed", result=result_payload)
    except Exception as e:
        logger.error(f"Background Audit Failed for {session_id}: {str(e)}")
        db_service.create_or_update_audit(session_id, video_url, video_id, status="failed", error=str(e))

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
    
    # Use user-provided name + short UUID to guarantee uniqueness for Azure Video Indexer
    if request.video_name:
        # Strip spaces and make safe, then append ID
        safe_name = request.video_name.replace(" ", "_")
        video_id_short = f"{safe_name}_{session_id[:8]}"
    else:
        video_id_short = f"vid_{session_id[:8]}" 
    
    #  LOG INCOMING REQUEST 
    logger.info(f"Received Audit Request: {request.video_url} (Name: {video_id_short}, Session: {session_id})")

    initial_inputs = {
        "video_url": request.video_url,  # From the API request
        "video_id": video_id_short,      # Custom name or generated ID
        "compliance_results": [],        # Will be populated by Auditor
        "errors": []                     # Tracks any processing errors
    }

    try:
        #  STORE JOB AND START BACKGROUND TASK
        db_service.create_or_update_audit(session_id, request.video_url, video_id_short, status="pending")
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
async def get_audit_status(session_id: str, video_id: Optional[str] = None):
    """
    Endpoint to check the real-time status of a background audit job.
    Uses a parameterized query to safely look up by session ID across partitions.
    """
    if db_service.client:
        # Parameterized cross-partition query — prevents query injection via the URL path.
        query = "SELECT * FROM c WHERE c.id = @session_id"
        params = [{"name": "@session_id", "value": session_id}]
        items = list(db_service.container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        ))
        if items:
            return items[0]
        raise HTTPException(status_code=404, detail="Job not found")
    else:
        # Fallback if DB is not configured (should not happen in prod)
        raise HTTPException(status_code=500, detail="Database not configured")

@app.get("/audits")
async def get_all_audits():
    """
    Endpoint to fetch audit history (lean metadata).
    """
    if db_service.client:
        return db_service.get_all_audits()
    else:
        return []

@app.delete("/audit/{session_id}")
async def delete_audit_record(session_id: str):
    """
    Endpoint to delete a specific audit from the history.
    """
    if db_service.client:
        success = db_service.delete_audit(session_id)
        if success:
            return {"message": "Audit deleted successfully."}
        raise HTTPException(status_code=404, detail="Audit not found or could not be deleted.")
    else:
        raise HTTPException(status_code=500, detail="Database not configured")

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