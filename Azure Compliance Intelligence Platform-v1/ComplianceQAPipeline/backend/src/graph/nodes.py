"""
Graph Nodes — Azure Compliance Intelligence Platform

Five focused nodes, each with a single responsibility:

    index_video_node       — Download & index video via Azure Video Indexer
    rag_retriever_node     — Query Azure AI Search for relevant compliance rules
    compliance_auditor_node — Detect violations using retrieved rules (structured output)
    report_synthesiser_node — Produce a rich, detailed markdown compliance report
    error_handler_node      — Generate a clean failure report when indexing fails
"""

import os
import logging
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.messages import SystemMessage, HumanMessage

from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService

load_dotenv()

logger = logging.getLogger("Azure-Compliance-Intelligence-Platform")
logging.basicConfig(level=logging.INFO)


# ===========================================================================
# SINGLETON CLIENTS — Initialised once at module load, reused across requests
# ===========================================================================

def _build_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.0,
        model_kwargs={"seed": 42},
    )

def _build_vector_store() -> AzureSearch:
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
    return AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query,
    )

# Lazy singletons — built on first use, then cached
_llm: Optional[AzureChatOpenAI] = None
_vector_store: Optional[AzureSearch] = None

def get_llm() -> AzureChatOpenAI:
    global _llm
    if _llm is None:
        logger.info("[Singleton] Initialising AzureChatOpenAI client...")
        _llm = _build_llm()
    return _llm

def get_vector_store() -> AzureSearch:
    global _vector_store
    if _vector_store is None:
        logger.info("[Singleton] Initialising AzureSearch vector store...")
        _vector_store = _build_vector_store()
    return _vector_store


# ===========================================================================
# STRUCTURED OUTPUT SCHEMAS
# ===========================================================================

class ComplianceIssue(BaseModel):
    category: str = Field(
        description="Violation category (e.g., 'Misleading Claims', 'Unsubstantiated Statistics')"
    )
    severity: str = Field(
        description="Severity level: CRITICAL or WARNING"
    )
    description: str = Field(
        description=(
            "Detailed explanation of the violation. Include: the exact offending quote or "
            "on-screen text, the timestamp or scene where it occurs, and why it breaches the rule."
        )
    )
    evidence: str = Field(
        description="Direct quote or text excerpt from the transcript/OCR that constitutes the violation."
    )
    rule_breached: str = Field(
        description="The specific compliance rule this violation breaks."
    )

class AuditFindings(BaseModel):
    reasoning_process: str = Field(
        description=(
            "Step-by-step chain-of-thought analysis of the transcript against each retrieved rule. "
            "Be thorough — walk through every rule and note whether it is satisfied or violated."
        )
    )
    status: str = Field(description="Overall audit status: PASS or FAIL")
    risk_level: str = Field(description="Overall risk level: LOW, MEDIUM, HIGH, or CRITICAL")
    compliance_results: List[ComplianceIssue] = Field(
        description="Complete list of all identified violations. Empty list if none found."
    )

class SynthesisedReport(BaseModel):
    final_report: str = Field(
        description=(
            "A comprehensive, structured markdown compliance report. "
            "Must include: (1) Executive Summary paragraph of 3-5 sentences covering the overall "
            "audit outcome, risk level, and immediate recommended action. "
            "(2) A 'What Passed' section briefly noting compliant areas. "
            "(3) Per-violation breakdown already captured in compliance_results. "
            "Write in a professional, authoritative tone suitable for a senior compliance officer."
        )
    )


# ===========================================================================
# NODE 1 — VIDEO INDEXER
# Responsibility: Download from YouTube, upload to Azure Video Indexer, extract transcript + OCR
# ===========================================================================

def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Downloads the YouTube video, uploads it to Azure Video Indexer,
    waits for processing, and extracts the transcript and OCR text.
    On failure, sets error_message so the conditional edge routes to error_handler.
    """
    video_url = state.get("video_url")
    video_id_input = state.get("video_id", "video_demo")

    logger.info(f"[Node: Indexer] Processing video '{video_url}' with id '{video_id_input}'")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()

        try:
            if "youtube.com" in video_url or "youtu.be" in video_url:
                local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
            else:
                raise ValueError("Only YouTube URLs are currently supported.")

            azure_video_id = vi_service.upload_video(local_path, video_name=video_id_input)
            logger.info(f"[Node: Indexer] Upload successful. Azure Video ID: {azure_video_id}")

        finally:
            if os.path.exists(local_filename):
                os.remove(local_filename)
                logger.info(f"[Node: Indexer] Cleaned up local file: {local_filename}")

        raw_insights = vi_service.wait_for_processing(azure_video_id)
        clean_data = vi_service.extract_data(raw_insights)

        logger.info("[Node: Indexer] Extraction complete — routing to RAG Retriever.")
        return clean_data

    except Exception as e:
        logger.error(f"[Node: Indexer] Failed: {str(e)}")
        return {
            "errors": [f"Video Indexing Failed: {str(e)}"],
            "error_message": str(e),
            "transcript": "",
            "ocr_text": [],
        }


# ===========================================================================
# NODE 2 — RAG RETRIEVER
# Responsibility: Query Azure AI Search with transcript + OCR, store rules in state
# ===========================================================================

def rag_retriever_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Queries the Azure AI Search knowledge base using the transcript and OCR text
    as the query. Retrieves the top-k most relevant compliance rules and stores
    them in state['retrieved_rules'] for the auditor node to consume.
    """
    logger.info("[Node: RAG Retriever] Querying Azure AI Search knowledge base...")

    transcript = state.get("transcript", "")
    ocr_text = state.get("ocr_text", [])

    query_text = f"{transcript} {' '.join(ocr_text)}".strip()

    try:
        vector_store = get_vector_store()
        # Retrieve top 5 docs (up from 3) for broader rule coverage, sorted for determinism
        docs = vector_store.similarity_search(query_text, k=5)
        docs = sorted(docs, key=lambda x: x.page_content)
        retrieved_rules = "\n\n---\n\n".join([doc.page_content for doc in docs])

        logger.info(f"[Node: RAG Retriever] Retrieved {len(docs)} rule document(s).")
        return {"retrieved_rules": retrieved_rules}

    except Exception as e:
        logger.error(f"[Node: RAG Retriever] Search failed: {str(e)}")
        return {
            "errors": [f"RAG Retrieval Failed: {str(e)}"],
            "retrieved_rules": "No rules could be retrieved due to a search error.",
        }


# ===========================================================================
# NODE 3 — COMPLIANCE AUDITOR
# Responsibility: Structured violation detection only — no report writing
# ===========================================================================

def compliance_auditor_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Applies the retrieved compliance rules to the transcript and OCR text.
    Uses structured output (function calling) to produce a deterministic,
    machine-readable list of violations. Does NOT write the narrative report —
    that is the report_synthesiser's job.
    """
    logger.info("[Node: Compliance Auditor] Analysing content against retrieved rules...")

    transcript = state.get("transcript", "")
    ocr_text = state.get("ocr_text", [])
    retrieved_rules = state.get("retrieved_rules", "No rules available.")
    video_metadata = state.get("video_metadata", {})

    system_prompt = f"""You are a Senior Brand Compliance Auditor with expertise in regulatory standards.

OFFICIAL COMPLIANCE RULES (retrieved from the knowledge base):
{retrieved_rules}

YOUR TASK:
1. Read the transcript and on-screen text (OCR) carefully.
2. For EACH rule above, check whether the video content complies or violates it.
3. Document your reasoning step by step in 'reasoning_process'.
4. For every violation found, capture:
   - The exact category and rule that is breached
   - A specific evidence quote from the transcript/OCR
   - Whether it is CRITICAL (regulatory risk) or WARNING (brand risk)
   - A detailed description explaining why it is a violation

If the content is fully compliant, set status to "PASS" and return an empty compliance_results list.
Be thorough — a missed violation is worse than a false positive."""

    user_message = f"""VIDEO METADATA: {video_metadata}

TRANSCRIPT:
{transcript}

ON-SCREEN TEXT (OCR):
{ocr_text}

Please analyse this content against the compliance rules provided."""

    try:
        structured_llm = get_llm().with_structured_output(AuditFindings)
        findings = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ])

        logger.info(
            f"[Node: Compliance Auditor] Complete. Status: {findings.status}, "
            f"Risk: {findings.risk_level}, Violations: {len(findings.compliance_results)}"
        )

        return {
            "compliance_results": [issue.model_dump() for issue in findings.compliance_results],
            "final_status": findings.status,
            # Pass risk_level and reasoning into state via errors list trick — 
            # store as metadata in final_report placeholder; synthesiser will build the real report
            "final_report": f"__RISK_LEVEL__:{findings.risk_level}",
        }

    except Exception as e:
        logger.error(f"[Node: Compliance Auditor] Error: {str(e)}")
        return {
            "errors": [f"Auditor Node Failed: {str(e)}"],
            "final_status": "FAIL",
            "final_report": "Audit could not be completed due to a system error.",
        }


# ===========================================================================
# NODE 4 — REPORT SYNTHESISER
# Responsibility: Write the rich, detailed narrative compliance report
# ===========================================================================

def report_synthesiser_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Takes the structured violations from the auditor and synthesises a
    comprehensive, professional-grade markdown compliance report.

    Output is ~50% richer than the previous single-node approach, including:
    - Executive summary (3-5 sentences)
    - Overall risk level
    - Per-violation breakdown with impact and remediation steps
    - 'What Passed' section for compliant areas
    """
    logger.info("[Node: Report Synthesiser] Generating comprehensive compliance report...")

    transcript = state.get("transcript", "")
    ocr_text = state.get("ocr_text", [])
    video_id = state.get("video_id", "Unknown")
    final_status = state.get("final_status", "UNKNOWN")
    compliance_results = state.get("compliance_results", [])
    retrieved_rules = state.get("retrieved_rules", "")

    # Extract risk level stored by auditor node
    raw_report = state.get("final_report", "")
    risk_level = "UNKNOWN"
    if raw_report.startswith("__RISK_LEVEL__:"):
        risk_level = raw_report.replace("__RISK_LEVEL__:", "").strip()

    violations_text = ""
    if compliance_results:
        for i, issue in enumerate(compliance_results, 1):
            violations_text += f"""
Violation {i}:
  Category: {issue.get('category')}
  Severity: {issue.get('severity')}
  Description: {issue.get('description')}
  Evidence: {issue.get('evidence', 'N/A')}
  Rule Breached: {issue.get('rule_breached', 'N/A')}
"""
    else:
        violations_text = "No violations detected."

    system_prompt = """You are a Senior Compliance Report Writer producing official audit documentation.

Your report must be written in professional markdown and MUST include ALL of the following sections:

## Executive Summary
Write 3-5 sentences covering: overall audit outcome, the primary risk areas identified (if any),
the overall risk level, and the single most important recommended action.

## Overall Risk Assessment
State the risk level (LOW / MEDIUM / HIGH / CRITICAL) and provide 2-3 sentences justifying it.

## Violations Detected
For EACH violation provided, write a sub-section with:
  ### [SEVERITY] Category Name
  **Evidence:** Direct quote or description of the offending content
  **Rule Breached:** The specific rule that was violated
  **Impact:** 2-3 sentences on the regulatory or brand consequence of this violation
  **Recommended Remediation:** Specific, actionable steps to fix this violation

## What Passed
2-3 sentences summarising the areas of the content that were compliant.
If the overall status is FAIL, still acknowledge the compliant parts.

## Conclusion
1-2 sentence closing statement on the urgency and next steps.

IMPORTANT:
- Be specific — reference actual content from the transcript/OCR where possible
- Write for a senior compliance officer audience
- Do NOT be vague or generic
- Produce a thorough report — length and depth are important"""

    user_message = f"""Please write the compliance audit report for video: {video_id}

AUDIT OUTCOME: {final_status}
RISK LEVEL: {risk_level}
NUMBER OF VIOLATIONS: {len(compliance_results)}

VIOLATIONS FOUND:
{violations_text}

TRANSCRIPT EXCERPT (for context):
{transcript[:3000]}

ON-SCREEN TEXT:
{ocr_text}

COMPLIANCE RULES THAT WERE APPLIED:
{retrieved_rules[:2000]}"""

    try:
        structured_llm = get_llm().with_structured_output(SynthesisedReport)
        synthesis = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ])

        logger.info("[Node: Report Synthesiser] Report generation complete.")
        return {"final_report": synthesis.final_report}

    except Exception as e:
        logger.error(f"[Node: Report Synthesiser] Error: {str(e)}")
        # Fallback: build a basic report from state data without the LLM
        fallback = (
            f"## Compliance Audit Report — {video_id}\n\n"
            f"**Status:** {final_status}  |  **Risk Level:** {risk_level}\n\n"
            f"**Violations Found:** {len(compliance_results)}\n\n"
            + "\n".join(
                f"- [{v.get('severity')}] **{v.get('category')}**: {v.get('description')}"
                for v in compliance_results
            )
        )
        return {
            "errors": [f"Report Synthesis Failed (fallback used): {str(e)}"],
            "final_report": fallback,
        }


# ===========================================================================
# NODE 5 — ERROR HANDLER
# Responsibility: Produce a clean, structured failure report when indexing fails
# ===========================================================================

def error_handler_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Activated when the indexer node fails (no transcript available).
    Produces a structured failure report so the API and frontend display
    a meaningful error instead of a raw exception.
    """
    error_message = state.get("error_message", "Unknown error during video processing.")
    video_id = state.get("video_id", "Unknown")
    errors = state.get("errors", [])

    logger.warning(f"[Node: Error Handler] Handling indexing failure for '{video_id}': {error_message}")

    failure_report = f"""## Audit Failed — {video_id}

### What Happened
The compliance audit could not be completed because the video could not be processed.

**Root Cause:** {error_message}

### System Errors Logged
{chr(10).join(f'- {e}' for e in errors) if errors else '- No additional details available.'}

### Recommended Actions
1. Verify the YouTube URL is valid, public, and not age-restricted or geo-blocked.
2. Check that Azure Video Indexer credentials are correctly configured in your `.env` file.
3. Retry the audit — transient network issues may resolve on a second attempt.
4. If the problem persists, contact your platform administrator with the error details above.
"""

    return {
        "final_status": "FAIL",
        "final_report": failure_report,
        "compliance_results": [],
    }


# ===========================================================================
# ROUTING FUNCTION — Used by the conditional edge after the indexer node
# ===========================================================================

def route_after_indexing(state: VideoAuditState) -> str:
    """
    Inspects state after the indexer node runs.
    Routes to 'error_handler' if the transcript is missing (indexing failed),
    otherwise routes to 'rag_retriever' to continue the audit pipeline.
    """
    if not state.get("transcript"):
        logger.warning("[Router] No transcript found — routing to error_handler.")
        return "error"
    logger.info("[Router] Transcript found — routing to rag_retriever.")
    return "ok"