from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from app.core.config.settings import get_settings

class TextProcessor:
    def __init__(self):
        settings = get_settings()
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.pre_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        self.chunker = SemanticChunker(
            self.embedding_model,
            breakpoint_threshold_type="percentile"
        )
    
    def process_text(self, text: str):
        # Pre-split text
        pre_chunks = self.pre_splitter.split_text(text)
        
        # Process chunks
        chunks = []
        for pre_chunk in pre_chunks:
            chunks.extend(self.chunker.split_text(pre_chunk))
        
        # Generate embeddings
        texts = [chunk for chunk in chunks]
        embeddings = self.embedding_model.embed_documents(texts)
        
        return chunks, embeddings 