import os
import streamlit as st
from mistralai import Mistral, DocumentURLChunk
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings  # Keep for embeddings
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv

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

# Initialize OpenAI embedding model
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Semantic chunker with pre-splitter
pre_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunker = SemanticChunker(embedding_model, breakpoint_threshold_type="percentile")

# Rough token counter
def count_tokens(text):
    return len(text) // 4

# Function to extract text from PDFs using Mistral OCR
def extract_text_from_pdfs(pdf_files):
    all_text = []
    for pdf_file in pdf_files:
        uploaded_file = mistral_client.files.upload(
            file={"file_name": pdf_file.name, "content": pdf_file.read()},
            purpose="ocr",
        )
        signed_url = mistral_client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        pdf_response = mistral_client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=False
        )
        markdown_text = "\n\n".join(page.markdown for page in pdf_response.pages)
        all_text.append({"file_name": pdf_file.name, "content": markdown_text})
        st.write(f"Extracted text from {pdf_file.name}: {markdown_text[:200]}...")
    return all_text

# Function to chunk documents with pre-splitting
def chunk_documents(documents):
    chunks = []
    for doc in documents:
        pre_chunks = pre_splitter.split_text(doc["content"])
        doc_chunks = []
        for pre_chunk in pre_chunks:
            doc_chunks.extend(chunker.split_text(pre_chunk))
        st.write(f"Created {len(doc_chunks)} chunks for {doc['file_name']}")
        for i, chunk in enumerate(doc_chunks):
            chunks.append({
                "text": chunk,
                "metadata": {"file_name": doc["file_name"], "chunk_id": i}
            })
            st.write(f"Chunk {i}: {chunk[:100]}...")
    return chunks

# Function to generate embeddings (using OpenAI)
def generate_embeddings(chunks):
    texts = [chunk["text"] for chunk in chunks]
    try:
        embeddings = embedding_model.embed_documents(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        return chunks
    except Exception as e:
        st.error(f"Error generating embeddings with OpenAI: {str(e)}")
        raise

# Function to store chunks in Supabase
def store_in_supabase(chunks):
    data = [{"text": chunk["text"], "embedding": chunk["embedding"], "metadata": chunk["metadata"]} for chunk in chunks]
    try:
        response = supabase.table("docs").insert(data).execute()
        st.write(f"Stored {len(response.data)} chunks in Supabase")
    except Exception as e:
        st.error(f"Error storing in Supabase: {str(e)}")

# Function to query Supabase (using OpenAI embedding)
def query_supabase(query_text, top_k=5):
    try:
        query_embedding = embedding_model.embed_query(query_text)
        response = supabase.rpc(
            "match_docs",
            {"query_embedding": query_embedding, "match_threshold": 0.3, "match_count": top_k}
        ).execute()
        st.write(f"Found {len(response.data)} matches for query: {query_text}")
        return response.data
    except Exception as e:
        st.error(f"Error querying Supabase with OpenAI embedding: {str(e)}")
        return []

# Function to generate answer using Gemini
def generate_answer(query, context):
    prompt_template = """You are a cybersecurity expert assistant with deep technical knowledge. Your task is to provide comprehensive, detailed answers based on the context provided below.

    CONTEXT:
    {context}
    
    QUESTION:
    {question}
    
    Instructions:
    1. First, carefully analyze all the provided context fragments to gather relevant information.
    2. Synthesize a complete, well-structured answer that incorporates information from ALL relevant context fragments don't miss any useful  information from context. 
    3. whenever necessary include specific details, examples, and technical explanations from the context do not generate the information by your knowledge. 
    4. Structure your answer with clear explanations of key concepts, and practical implications and do not generate information on your knowledge.
    5. Make your response detailed and thorough - aim for completeness rather than brevity.
    6. Use only information present in the context - do not add external knowledge.
    7. If the context is insufficient, clearly state I don not have sufficient information to answer, do not mention any other information.
    
    Provide a thorough, detailed response that fully addresses the question using all relevant information from the context:"""
    
    full_prompt = prompt_template.format(context=context, question=query)
    try:
        response = gemini_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,  # Slightly higher for better elaboration
                top_p=0.95,
                max_output_tokens=2048,  # Increased output length
                presence_penalty=0.1,  # Encourage broader coverage
                frequency_penalty=0.1  # Discourage repetition
            ),
            stream=True
        )
        response_text = "".join([part.text for part in response])
        return response_text
    except Exception as e:
        st.error(f"Error generating answer with Gemini: {str(e)}")
        return "Sorry, I couldn't generate an answer due to an error."


# Streamlit app
def main():
    st.title("Cybersecurity PDF RAG System with Mistral OCR")
    st.write("Upload cybersecurity PDFs and ask questions!")

    with st.sidebar:
        st.header("Upload PDFs")
        uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
        if st.button("Process PDFs"):
            if uploaded_files:
                with st.spinner("Extracting text with Mistral OCR and processing..."):
                    documents = extract_text_from_pdfs(uploaded_files)
                    chunks = chunk_documents(documents)
                    chunks_with_embeddings = generate_embeddings(chunks)
                    store_in_supabase(chunks_with_embeddings)
                    st.success(f"Processed and stored {len(chunks)} chunks!")
            else:
                st.error("Please upload at least one PDF.")

    st.header("Ask a Cybersecurity Question")
    query = st.text_input("Enter your question (e.g., 'What are common cybersecurity threats?'):")
    num_chunks = st.slider("Number of chunks to retrieve", min_value=1, max_value=10, value=5)
    if st.button("Search"):
        if query:
            with st.spinner("Searching..."):
                results = query_supabase(query, top_k=num_chunks)
                if results:
                    max_context_tokens = 15000  # Adjustable for Gemini’s larger context
                    context = ""
                    for result in results:
                        chunk_text = f"Document: {result['metadata']['file_name']}, Chunk {result['metadata']['chunk_id']}:\n{result['text']}"
                        if count_tokens(context + chunk_text) < max_context_tokens:
                            context += chunk_text + "\n\n"
                        else:
                            st.warning(f"Stopped at {len(context.splitlines())//2} chunks to stay under token limit.")
                            break
                    with st.spinner("Generating answer..."):
                        answer = generate_answer(query, context)
                    st.subheader("Answer")
                    st.write(answer)
                    with st.expander("See source chunks"):
                        st.subheader("Source Chunks")
                        used_chunks = len(context.splitlines())//2 if context else 0
                        for i, result in enumerate(results[:used_chunks], 1):
                            st.write(f"**Source {i} (Similarity: {result['similarity']:.3f})**")
                            st.write(f"From: {result['metadata']['file_name']}")
                            st.write(f"Text: {result['text']}")
                            st.write("---")
                else:
                    st.write("No relevant chunks found.")
        else:
            st.error("Please enter a question.")

if __name__ == "__main__":
    main()