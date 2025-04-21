from mistralai import Mistral, DocumentURLChunk
from app.core.config.settings import get_settings

class OCRService:
    def __init__(self):
        settings = get_settings()
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
    
    async def process_pdf(self, file_content: bytes, file_name: str):
        # Upload file to Mistral
        uploaded_file = self.client.files.upload(
            file={"file_name": file_name, "content": file_content},
            purpose="ocr",
        )
        
        # Get signed URL and process OCR
        signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        pdf_response = self.client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=False
        )
        
        # Extract text from PDF
        markdown_text = "\n\n".join(page.markdown for page in pdf_response.pages)
        return markdown_text 