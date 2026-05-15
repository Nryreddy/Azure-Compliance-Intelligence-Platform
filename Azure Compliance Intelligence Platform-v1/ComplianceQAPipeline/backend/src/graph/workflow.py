"""
 workflow - its nothing but connecting all the nodes, state  together and execute it in order

This module defines the DAG : Directed Acyclic Graph that orchestrates the entire compliance monitoring and QA pipeline.

it connects the nodes using StateGraph from LangGraph library. it is a wrapper around LangChain expression language (LCEL)

START -> index_video_node - > audit_content_node -> END

"""
from langgraph.graph import StateGraph, END

# Import the State Schema
from backend.src.graph.state import VideoAuditState

# Import the Functional Nodes
from backend.src.graph.nodes import (
    index_video_node,
    audit_content_node
)

def create_graph():
    """
    Constructs and compiles the LangGraph workflow.

    Returns:
        CompiledGraph: A runnable graph object ready for execution.
    """
    # 1. Initialize the Graph with the State Schema
    # This ensures all nodes adhere to the 'VideoAuditState' data structure.
    workflow = StateGraph(VideoAuditState)

    # 2. Add Nodes (The Workers)
    # The first argument is the unique name of the node in the graph.
    # The second argument is the function to execute.
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audit_content_node)

    # 3. Define Edges (The Logic Flow)
    # Define the entry point: When the graph starts, go to 'indexer'.
    workflow.set_entry_point("indexer")

    # Connect 'indexer' -> 'auditor'
    # Once the video is indexed (transcript extracted), move to compliance auditing.
    workflow.add_edge("indexer", "auditor")

    # Connect 'auditor' -> END
    # Once the audit is complete, the workflow finishes.
    workflow.add_edge("auditor", END)

    # 4. Compile the Graph
    # This validates the connections and creates the executable runnable.
    app = workflow.compile()

    return app

# Expose the runnable app for import by the API or CLI
app = create_graph()