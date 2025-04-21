from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai import Mistral, DocumentURLChunk
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv
import os

from service.query_service import query_supabase
from service.answer_service import generate_answer

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mistral_client = Mistral(api_key=MISTRAL_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-pro')
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Initialize chunkers
pre_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunker = SemanticChunker(embedding_model, breakpoint_threshold_type="percentile")

app = FastAPI(title="PDF Processing API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def count_tokens(text):
    return len(text) // 4

@app.get("/")
async def root():
    return {"message": "Welcome to PDF Processing API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        print("Reading file content...")
        file_content = await file.read()
        
        print("Uploading file to Mistral...")
        uploaded_file = mistral_client.files.upload(
            file={"file_name": file.filename, "content": file_content},
            purpose="ocr",
        )
        print(f"File uploaded successfully. File ID: {uploaded_file.id}")
        
        print("Getting signed URL...")
        signed_url = mistral_client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        print(f"Signed URL obtained: {signed_url.url}")
        
        print("Processing OCR...")
        pdf_response = mistral_client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=False
        )
        print("OCR processing completed successfully")
        
        print("Extracting text from PDF...")
        markdown_text = "\n\n".join(page.markdown for page in pdf_response.pages)
        print(f"Extracted text length: {len(markdown_text)} characters")
        
        print("Pre-splitting text...")
        pre_chunks = pre_splitter.split_text(markdown_text)
        print(f"Number of pre-chunks: {len(pre_chunks)}")
        
        print("Processing chunks with semantic chunker...")
        chunks = []
        for pre_chunk in pre_chunks:
            chunks.extend(chunker.split_text(pre_chunk))
        print(f"Number of final chunks: {len(chunks)}")
        
        print("Generating embeddings...")
        texts = [chunk for chunk in chunks]
        embeddings = embedding_model.embed_documents(texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        print("Preparing data for Supabase...")
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
        
        print("Storing data in Supabase...")
        try:
            response = supabase.table("docs").insert(data).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error storing in Supabase: {str(e)}")
        print("Data stored successfully in Supabase")
        
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

class QuestionRequest(BaseModel):
    query: str
    num_chunks: int = 5

@app.post("/ask-question")
async def ask_question(request: Request):
    try:
        raw_body = await request.json()
        print(f"Raw request body: {raw_body}")
        question_request = QuestionRequest(**raw_body)
        print(f"Validated query: {question_request.query}, num_chunks: {question_request.num_chunks}")
        
        results = query_supabase(question_request.query, top_k=question_request.num_chunks)
        print(f"Supabase results: {len(results)} chunks found")
        if not results:
            print("No relevant chunks found in Supabase")
            return {"message": "No relevant chunks found."}

        max_context_tokens = 15000
        context = ""
        for result in results:
            chunk_text = f"Document: {result['metadata']['file_name']}, Chunk {result['metadata']['chunk_id']}:\n{result['text']}"
            if count_tokens(context + chunk_text) < max_context_tokens:
                context += chunk_text + "\n\n"
            else:
                print(f"Stopped at {len(context.splitlines())//2} chunks to stay under token limit")
                break
        print(f"Context length: {len(context)} characters")

        answer = generate_answer(question_request.query, context)
        print(f"Generated answer: {answer}")
        return {"answer": answer}
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))