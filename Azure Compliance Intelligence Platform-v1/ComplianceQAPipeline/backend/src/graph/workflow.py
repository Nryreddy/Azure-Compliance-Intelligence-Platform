"""
Workflow — Agentic LangGraph Compliance Pipeline

Defines the 5-node directed graph that orchestrates the full compliance audit.

Architecture:

    START
      │
      ▼
    [indexer]  ──── (no transcript / error) ────► [error_handler] ──► END
      │
      ▼ (transcript present)
    [rag_retriever]          Queries Azure AI Search for relevant compliance rules
      │
      ▼
    [compliance_auditor]     Structured violation detection using retrieved rules
      │
      ▼
    [report_synthesiser]     Produces rich, detailed markdown compliance report
      │
      ▼
      END
"""

from langgraph.graph import StateGraph, END, START

from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import (
    index_video_node,
    rag_retriever_node,
    compliance_auditor_node,
    report_synthesiser_node,
    error_handler_node,
    route_after_indexing,
)


def create_graph():
    """
    Constructs and compiles the agentic LangGraph compliance workflow.

    Returns:
        CompiledGraph: A runnable graph ready for invocation by the API or CLI.
    """
    workflow = StateGraph(VideoAuditState)

    # -----------------------------------------------------------------------
    # 1. Register nodes
    # -----------------------------------------------------------------------
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("compliance_auditor", compliance_auditor_node)
    workflow.add_node("report_synthesiser", report_synthesiser_node)
    workflow.add_node("error_handler", error_handler_node)

    # -----------------------------------------------------------------------
    # 2. Entry point
    # -----------------------------------------------------------------------
    workflow.set_entry_point("indexer")

    # -----------------------------------------------------------------------
    # 3. Conditional edge after indexer
    #    route_after_indexing() inspects state and returns "ok" or "error"
    # -----------------------------------------------------------------------
    workflow.add_conditional_edges(
        "indexer",
        route_after_indexing,
        {
            "ok": "rag_retriever",       # Transcript present → continue audit
            "error": "error_handler",    # No transcript → surface clean failure
        },
    )

    # -----------------------------------------------------------------------
    # 4. Linear edges through the happy path
    # -----------------------------------------------------------------------
    workflow.add_edge("rag_retriever", "compliance_auditor")
    workflow.add_edge("compliance_auditor", "report_synthesiser")

    # -----------------------------------------------------------------------
    # 5. Terminal edges
    # -----------------------------------------------------------------------
    workflow.add_edge("report_synthesiser", END)
    workflow.add_edge("error_handler", END)

    # -----------------------------------------------------------------------
    # 6. Compile
    # -----------------------------------------------------------------------
    return workflow.compile()


# Singleton compiled graph — imported by server.py and main.py
app = create_graph()