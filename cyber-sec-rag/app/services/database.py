from supabase import create_client, Client
from app.core.config.settings import get_settings
from typing import List, Dict, Any

class DatabaseService:
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    def store_documents(self, data: List[Dict[str, Any]]):
        response = self.client.table("docs").insert(data).execute()
        return response
    
    def query_documents(self, query_embedding: List[float], match_threshold: float = 0.3, match_count: int = 5):
        response = self.client.rpc(
            "match_docs",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count
            }
        ).execute()
        return response.data 