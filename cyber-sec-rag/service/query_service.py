from app_gem import embedding_model, supabase

def query_supabase(query_text, top_k=5):
    try:
        query_embedding = embedding_model.embed_query(query_text)
        response = supabase.rpc(
            "match_docs",
            {"query_embedding": query_embedding, "match_threshold": 0.3, "match_count": top_k}
        ).execute()
        print(f"Supabase query response: {len(response.data)} results")
        return response.data
    except Exception as e:
        print(f"Supabase query error: {str(e)}")
        raise RuntimeError(f"Error querying Supabase: {str(e)}")