import os           
import logging     
from azure.monitor.opentelemetry import configure_azure_monitor  

# This separates telemetry logs from your main application logs
logger = logging.getLogger("AI-COMPLIANCE-PLATFORM-TELEMETRY")


def setup_telemetry():
    """
    Initializes Azure Monitor OpenTelemetry.
    - Industry-standard observability framework
    - Tracks: HTTP requests, database queries, errors, performance metrics
    - Sends this data to Azure Monitor 
    """
    # Reads the Azure Monitor 
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    # CHECK IF CONFIGURED
    if not connection_string:
        # If the environment variable is missing/empty, telemetry won't work
        # 
        logger.warning("No Instrumentation Key found. Telemetry is DISABLED.")
        return  # Exit function early - don't try to configure Azure Monitor

    # CONFIGURE AZURE MONITOR
    try:
        # configure_azure_monitor() does the heavy lifting:
        # 1. Registers automatic instrumentation for:
        #    - HTTP requests (FastAPI endpoints)
        #    - Database calls (Azure Search queries)
        #    - Logging events
        # 2. Starts background thread to send data to Azure
        configure_azure_monitor(
            connection_string=connection_string,  # Where to send data
            logger_name="AI-COMPLIANCE-PLATFORM-TELEMETRY"   # Optional: custom tracer name
        )
        logger.info(" Azure Monitor Tracking Enabled & Connected!")
        
    except Exception as e: 
        logger.error(f"Failed to initialize Azure Monitor: {e}")