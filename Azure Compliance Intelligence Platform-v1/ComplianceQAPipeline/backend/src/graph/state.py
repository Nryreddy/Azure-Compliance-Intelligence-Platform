from typing import TypedDict, Annotated, Optional, List, Dict, Any
import operator
from langgraph.graph import MessageState, StateGraph, END, START

class ComplianceIssue(TypedDict):
    """Represents a compliance issue."""
    category: str
    description: str # detail of the violation
    severity: str # critical or warning
    timestamp: Optional[str]
    

# define global graph state
class VideoAuditState(TypedDict):
    """Defines the data schema for langgraph execution content
    Main container - holds all the information about the audit
    from the inintial url to the final report"""
    #input parameters 
    video_url: str
    video_id: str

    # ingestion and extraction data    -from the video url
    local_file_path : Optional[str]
    video_metadata : Dict[str,Any]
    transcript : Optional[str]
    ocr_text : List[str]

    #analysis output
    # stores the list of compliance issues found in the video
    compliance_results : Annotated[List[ComplianceIssue],operator.add]

    # final status
    final_status : str # PASS|FAIL
    final_report : str # markdown format

    # system observability 
    # errors : API timeout, list of system level errors
    errors : Annotated[List[str],operator.add]




        
    



