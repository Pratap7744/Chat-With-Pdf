from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.ocr_service import OCRService
from app.services.text_processor import TextProcessor
from app.services.database import DatabaseService
from app.services.qa_service import QAService
from typing import List, Dict, Any

router = APIRouter()

# Initialize services
ocr_service = OCRService()
text_processor = TextProcessor()
db_service = DatabaseService()
qa_service = QAService()

@router.get("/")
async def root():
    return {"message": "Welcome to PDF Processing API"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process PDF with OCR
        markdown_text = await ocr_service.process_pdf(file_content, file.filename)
        
        # Process text and generate embeddings
        chunks, embeddings = text_processor.process_text(markdown_text)
        
        # Prepare data for database
        data = [
            {
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    "file_name": file.filename,
                    "chunk_id": i
                }
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # Store in database
        db_service.store_documents(data)
        
        return {
            "message": "PDF processed successfully",
            "num_chunks": len(chunks),
            "file_name": file.filename
        }
        
    except Exception as e:
        error_detail = str(e)
        if not error_detail:
            error_detail = f"An error occurred: {type(e).__name__}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/ask-question")
async def ask_question(query: str, num_chunks: int = 5):
    try:
        print("hello")
        # Generate query embedding
        query_embedding = text_processor.embedding_model.embed_query(query)
        
        # Query database for relevant chunks
        results = db_service.query_documents(
            query_embedding=query_embedding,
            match_count=num_chunks
        )
        
        if not results:
            return {"message": "No relevant chunks found."}
        
        # Prepare context from results
        max_context_tokens = 15000
        context = ""
        for result in results:
            chunk_text = f"Document: {result['metadata']['file_name']}, Chunk {result['metadata']['chunk_id']}:\n{result['text']}"
            if len(context) + len(chunk_text) < max_context_tokens:
                context += chunk_text + "\n\n"
            else:
                break
        
        # Generate answer
        answer = qa_service.generate_answer(query, context)
        
        return {
            "answer": answer,
            "sources": [
                {
                    "file_name": result['metadata']['file_name'],
                    "chunk_id": result['metadata']['chunk_id'],
                    "similarity": result.get('similarity', 0)
                }
                for result in results
            ]
        }
        
    except Exception as e:
        error_detail = str(e)
        if not error_detail:
            error_detail = f"An error occurred: {type(e).__name__}"
        raise HTTPException(status_code=500, detail=error_detail) 