import json
import os
import logging
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

#import sate schema

from backend.src.graph.state import VideoAuditState

#import service 
from backend.src.services.video_indexer import VideoIndexerService

# connfigure the logger
logger = logging.getLogger("Azure-Compliance-Intelligence-Platform")
logging.basicConfig(level=logging.INFO)


# NODE 1 : Indexer
# func responsible for converting youtube video into text
def index_video_node(state:VideoAuditState) -> Dict[str,Any]:
    """
    Download youtube video from url
    Index the video in Azure Video Indexer and extract metadata (insights)
    """
    
    video_url = state.get("video_url")
    video_id_input = state.get("video_id","video_demo")

    logger.info(f"-----[Node:Indexer] Processing video {video_url} with id {video_id_input}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()

        try:
            #download   - yt-dlp library used for downloading youtube video
            if "youtube.com" in video_url or "youtu.be" in video_url:
                local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
            else:
                raise Exception("Please provide valid youtube url")
            
            #upload - from local to azure video indexer
            azure_video_id = vi_service.upload_video(local_path,video_name=video_id_input)
             
            logger.info(f"Upload Successful. Azure ID : {azure_video_id}")
        finally:
            #cleanup - remove local file
            if os.path.exists(local_filename):
                os.remove(local_filename)
                logger.info(f"Deleted Local File : {local_filename}")

        #wait - until video is processed and insights are extracted --- pauses the code
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        #extract insights
        clean_data = vi_service.extract_data(raw_insights)

        logger.info(f"----[NODE: Indexer] Extraction Complete-----------")
        return clean_data
        
    except Exception as e:
        logger.error(f"----[NODE: Indexer] Video Indexing Failed : {str(e)}")
        return {
            "errors" : [f"Video Indexing Failed : {str(e)}"],
            "final_status": "FAIL",
            "transcript":"",
            "ocr_text" : []
        }
        
# --- NODE 2: THE COMPLIANCE AUDITOR ---
def audit_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Performs Retrieval-Augmented Generation (RAG) to audit the content.
    """
    logger.info("--- [Node: Auditor] querying Knowledge Base & LLM ---")
    
    transcript = state.get("transcript", "")
    
    if not transcript:
        logger.warning("No transcript available. Skipping Audit.")
        return {
            "final_status": "FAIL",
            "final_report": "Audit skipped because video processing failed (No Transcript)."
        }

    # Initialize Clients
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )
    
    # RAG Retrieval
    ocr_text = state.get("ocr_text", [])
    query_text = f"{transcript} {' '.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    
    retrieved_rules = "\n\n".join([doc.page_content for doc in docs])
    
    # --- UPDATED PROMPT WITH STRICT SCHEMA ---
    system_prompt = f"""
    You are a Senior Brand Compliance Auditor.
    
    OFFICIAL REGULATORY RULES:
    {retrieved_rules}
    
    INSTRUCTIONS:
    1. Analyze the Transcript and OCR text below.
    2. Identify ANY violations of the rules.
    3. Return strictly JSON in the following format:
    
    {{
        "compliance_results": [
            {{
                "category": "Claim Validation",
                "severity": "CRITICAL",
                "description": "Explanation of the violation..."
            }}
        ],
        "status": "FAIL", 
        "final_report": "Summary of findings..."
    }}

    If no violations are found, set "status" to "PASS" and "compliance_results" to [].
    """

    user_message = f"""
    VIDEO METADATA: {state.get('video_metadata', {})}
    TRANSCRIPT: {transcript}
    ON-SCREEN TEXT (OCR): {ocr_text}
    """

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        # --- Clean the (data) Markdown if present (```json ... ```) ---
        content = response.content
        if "```" in content:
            # Regex to find JSON inside code blocks
            content = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL).group(1)
            
        audit_data = json.loads(content.strip())
        
        # store the compliance results in the state 
        # and return the final status and report - as python dict
        return {
            "compliance_results": audit_data.get("compliance_results", []),
            "final_status": audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report", "No report generated.")
        }

    except Exception as e:
        logger.error(f"System Error in Auditor Node: {str(e)}")
        # Log the raw response to see what went wrong
        logger.error(f"Raw LLM Response: {response.content if 'response' in locals() else 'None'}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL"
        }