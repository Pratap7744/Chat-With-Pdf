# FastAPI Server

A basic FastAPI server with health check endpoint.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the server using uvicorn:
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000/api/v1`

## API Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `POST /upload-pdf`: Uploads pdf
- `POST /ask-question`: Sends query and returns answer

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 