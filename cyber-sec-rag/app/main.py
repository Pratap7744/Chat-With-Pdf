from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config.settings import get_settings

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="PDF Processing API",
    description="API for processing PDFs and answering questions based on their content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

# Global error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {"detail": str(exc)} 