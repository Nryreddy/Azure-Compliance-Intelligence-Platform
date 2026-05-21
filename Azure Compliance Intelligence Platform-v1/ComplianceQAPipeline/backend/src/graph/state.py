from typing import TypedDict, Annotated, Optional, List, Dict, Any
import operator
from langgraph.graph import StateGraph, END, START


class ComplianceIssue(TypedDict):
    """Represents a single compliance violation found in the video."""
    category: str
    description: str    # Detailed explanation with timestamp/text evidence
    severity: str       # CRITICAL or WARNING


# ---------------------------------------------------------------------------
# Global graph state — shared across all nodes in the workflow
# ---------------------------------------------------------------------------
class VideoAuditState(TypedDict):
    """
    Master state container for the compliance audit workflow.

    Fields flow through nodes in this order:
        Input → Indexer → RAG Retriever → Auditor → Synthesiser → Output
    """

    # --- Input ---
    video_url: str
    video_id: str

    # --- Ingestion / Extraction (populated by indexer node) ---
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]

    # --- RAG context (populated by rag_retriever node) ---
    retrieved_rules: Optional[str]       # Full text of retrieved compliance rules

    # --- Analysis output (populated by auditor node) ---
    compliance_results: Annotated[List[ComplianceIssue], operator.add]

    # --- Report output (populated by synthesiser node) ---
    final_status: str     # PASS | FAIL
    final_report: str     # Rich markdown report

    # --- Error handling ---
    error_message: Optional[str]                   # Set by error_handler node
    errors: Annotated[List[str], operator.add]     # Cumulative system-level errors
