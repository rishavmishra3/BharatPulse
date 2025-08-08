from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services and models
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.nlp_service import NLPService
from app.database import create_tables

app = FastAPI(title="BharatPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
stt_service = None
tts_service = None
nlp_service = None

@app.on_event("startup")
async def startup_event():
    global stt_service, tts_service, nlp_service
    
    # Create database tables
    create_tables()
    
    # Initialize services
    stt_service = STTService()
    tts_service = TTSService()
    nlp_service = NLPService()
    
    print("✅ BharatPulse API started successfully!")

@app.get("/")
async def root():
    return {"message": "BharatPulse API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": "operational"}

@app.post("/api/process-voice")
async def process_voice(
    audio_file: UploadFile = File(...),
    question_id: str = None,
    user_lang: str = "hi"
):
    """Process voice input and return structured response"""
    try:
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio content
        audio_content = await audio_file.read()
        
        # Speech to text
        transcription_result = await stt_service.transcribe(audio_content, user_lang)
        
        if not transcription_result.get("success"):
            return JSONResponse(
                status_code=400,
                content={"error": "Speech recognition failed", "success": False}
            )
        
        # Extract structured data
        extraction_result = await nlp_service.extract_fields(
            transcription_result.get("text", ""), question_id
        )
        
        return {
            "transcription": transcription_result,
            "extracted_data": extraction_result,
            "confidence": extraction_result.get("confidence", 0.0),
            "success": True
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/api/tts/{text}")
async def text_to_speech(text: str, lang: str = "hi"):
    """Convert text to speech"""
    try:
        audio_data = await tts_service.synthesize(text, lang)
        return {"audio_base64": audio_data, "success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
