from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

Base = declarative_base()

class ResponseDB(Base):
    __tablename__ = "survey_responses"
    
    id = Column(String, primary_key=True, index=True)
    survey_id = Column(String, nullable=False, index=True)
    respondent_id = Column(String, index=True)
    responses = Column(JSON, nullable=False)
    location_lat = Column(Float)
    location_lng = Column(Float)
    device_info = Column(JSON)
    audio_files = Column(JSON)  # Store audio file references
    verification_data = Column(JSON)  # Face/voice verification results
    confidence_scores = Column(JSON)  # Per-question confidence
    is_complete = Column(Boolean, default=False)
    is_synced = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AudioFileDB(Base):
    __tablename__ = "audio_files"
    
    id = Column(String, primary_key=True, index=True)
    response_id = Column(String, nullable=False, index=True)
    question_id = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    transcription = Column(Text)
    confidence = Column(Float)
    language = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic models for API
class LocationData(BaseModel):
    latitude: float
    longitude: float

class DeviceInfo(BaseModel):
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    device_id: Optional[str] = None

class VerificationData(BaseModel):
    face_verified: bool = False
    voice_verified: bool = False
    face_confidence: float = 0.0
    voice_confidence: float = 0.0
    respondent_hash: Optional[str] = None
    is_duplicate: bool = False

class ResponseModel(BaseModel):
    id: str
    survey_id: str
    respondent_id: Optional[str] = None
    responses: Dict[str, Any]
    location: Optional[LocationData] = None
    device_info: Optional[DeviceInfo] = None
    verification_data: Optional[VerificationData] = None
    confidence_scores: Optional[Dict[str, float]] = None
    is_complete: bool = False
    created_at: datetime = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ResponseCreateRequest(BaseModel):
    survey_id: str
    respondent_id: Optional[str] = None
    responses: Dict[str, Any]
    location: Optional[LocationData] = None
    device_info: Optional[DeviceInfo] = None
    verification_data: Optional[VerificationData] = None
    confidence_scores: Optional[Dict[str, float]] = None

class ResponseUpdateRequest(BaseModel):
    responses: Optional[Dict[str, Any]] = None
    location: Optional[LocationData] = None
    verification_data: Optional[VerificationData] = None
    confidence_scores: Optional[Dict[str, float]] = None
    is_complete: Optional[bool] = None

class AudioFileModel(BaseModel):
    id: str
    response_id: str
    question_id: str
    transcription: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = None
    created_at: datetime

class BatchSyncRequest(BaseModel):
    responses: List[ResponseModel]
    audio_files: Optional[List[Dict[str, Any]]] = None

class SyncStatusResponse(BaseModel):
    total_responses: int
    synced_responses: int
    failed_responses: int
    errors: List[str] = []
