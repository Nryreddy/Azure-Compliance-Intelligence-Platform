import os
import logging
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions

logger = logging.getLogger("CosmosDB-Service")

class DatabaseService:
    def __init__(self):
        self.endpoint = os.getenv("COSMOS_ENDPOINT")
        self.key = os.getenv("COSMOS_KEY")
        self.database_name = "ComplianceDB"
        self.container_name = "Audits"
        
        if not self.endpoint or not self.key:
            logger.warning("COSMOS_ENDPOINT or COSMOS_KEY not found. Database features will fail.")
            self.client = None
            return

        self.client = CosmosClient(self.endpoint, self.key)
        
        try:
            # Create database if it doesn't exist
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            
            # Create container if it doesn't exist
            # We partition by 'video_id' since we often lookup by video
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name, 
                partition_key=PartitionKey(path="/video_id")
            )
            logger.info("Connected to Cosmos DB successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {e}")
            self.client = None

    def create_or_update_audit(self, session_id: str, video_url: str, video_id: str, status: str, result: dict = None, error: str = None):
        """Creates or updates a record in Cosmos DB"""
        if not self.client:
            return

        # Cosmos DB requires an 'id' field as the unique identifier for the document
        document = {
            "id": session_id,
            "video_id": video_id,
            "video_url": video_url,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if result:
            document["result"] = result
        if error:
            document["error"] = error

        try:
            self.container.upsert_item(document)
        except Exception as e:
            logger.error(f"Error upserting document {session_id}: {e}")

    def get_audit(self, session_id: str, video_id: str):
        """Fetches a specific audit by session ID"""
        if not self.client:
            return None
        try:
            # Read item requires both the item ID and the Partition Key
            return self.container.read_item(item=session_id, partition_key=video_id)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error fetching document {session_id}: {e}")
            return None

    def get_all_audits(self):
        """Fetches a list of all audits (lean query without full results)"""
        if not self.client:
            return []
            
        query = "SELECT c.id, c.video_id, c.video_url, c.status, c.timestamp, c.result.status AS compliance_status FROM c ORDER BY c.timestamp DESC"
        try:
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return []

    def delete_audit(self, session_id: str) -> bool:
        """Deletes an audit record from Cosmos DB by first looking up its partition key (video_id)"""
        if not self.client:
            return False
        try:
            # We must fetch the item to get its partition key (video_id) for deletion.
            # Use parameterized query to prevent injection attacks.
            query = "SELECT c.id, c.video_id FROM c WHERE c.id = @session_id"
            params = [{"name": "@session_id", "value": session_id}]
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            if not items:
                logger.warning(f"Document {session_id} not found to delete.")
                return False
            
            video_id = items[0]["video_id"]
            self.container.delete_item(item=session_id, partition_key=video_id)
            logger.info(f"Deleted document {session_id} successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {session_id}: {e}")
            return False

# Singleton instance
db_service = DatabaseService()
