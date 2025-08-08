from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.response import (
    ResponseModel, ResponseCreateRequest, ResponseUpdateRequest,
    ResponseDB, AudioFileDB, BatchSyncRequest, SyncStatusResponse
)
from ..database import get_db
from ..utils.privacy import PrivacyService
import uuid
import json
from datetime import datetime

router = APIRouter()
privacy_service = PrivacyService()

@router.post("/surveys/{survey_id}/responses", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_response(
    survey_id: str,
    response_request: ResponseCreateRequest,
    db: Session = Depends(get_db)
):
    """Create new survey response"""
    response_id = str(uuid.uuid4())
    
    # Encrypt sensitive data
    encrypted_responses = privacy_service.encrypt_sensitive_data(response_request.responses)
    
    db_response = ResponseDB(
        id=response_id,
        survey_id=survey_id,
        respondent_id=response_request.respondent_id,
        responses=encrypted_responses,
        location_lat=response_request.location.latitude if response_request.location else None,
        location_lng=response_request.location.longitude if response_request.location else None,
        device_info=response_request.device_info.dict() if response_request.device_info else None,
        verification_data=response_request.verification_data.dict() if response_request.verification_data else None,
        confidence_scores=response_request.confidence_scores
    )
    
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return _convert_db_to_model(db_response)

@router.get("/surveys/{survey_id}/responses", response_model=List[ResponseModel])
async def get_survey_responses(
    survey_id: str,
    skip: int = 0,
    limit: int = 100,
    complete_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get responses for specific survey"""
    query = db.query(ResponseDB).filter(ResponseDB.survey_id == survey_id)
    
    if complete_only:
        query = query.filter(ResponseDB.is_complete == True)
    
    responses = query.offset(skip).limit(limit).all()
    
    return [_convert_db_to_model(response) for response in responses]

@router.get("/responses/{response_id}", response_model=ResponseModel)
async def get_response(response_id: str, db: Session = Depends(get_db)):
    """Get specific response by ID"""
    response = db.query(ResponseDB).filter(ResponseDB.id == response_id).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    return _convert_db_to_model(response)

@router.put("/responses/{response_id}", response_model=ResponseModel)
async def update_response(
    response_id: str,
    response_request: ResponseUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update existing response"""
    response = db.query(ResponseDB).filter(ResponseDB.id == response_id).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Update fields
    if response_request.responses:
        encrypted_responses = privacy_service.encrypt_sensitive_data(response_request.responses)
        response.responses = encrypted_responses
    
    if response_request.location:
        response.location_lat = response_request.location.latitude
        response.location_lng = response_request.location.longitude
    
    if response_request.verification_data:
        response.verification_data = response_request.verification_data.dict()
    
    if response_request.confidence_scores:
        response.confidence_scores = response_request.confidence_scores
    
    if response_request.is_complete is not None:
        response.is_complete = response_request.is_complete
    
    db.commit()
    db.refresh(response)
    
    return _convert_db_to_model(response)

@router.post("/responses/{response_id}/audio")
async def upload_audio_file(
    response_id: str,
    question_id: str,
    audio_file: UploadFile = File(...),
    transcription: Optional[str] = None,
    confidence: Optional[float] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload audio file for response"""
    # Verify response exists
    response = db.query(ResponseDB).filter(ResponseDB.id == response_id).first()
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Save audio file
    import os
    import aiofiles
    
    audio_id = str(uuid.uuid4())
    file_extension = audio_file.filename.split('.')[-1]
    file_path = f"audio_files/{response_id}/{audio_id}.{file_extension}"
    
    # Create directory if not exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await audio_file.read()
        await f.write(content)
    
    # Create database record
    db_audio = AudioFileDB(
        id=audio_id,
        response_id=response_id,
        question_id=question_id,
        file_path=file_path,
        transcription=transcription,
        confidence=confidence,
        language=language
    )
    
    db.add(db_audio)
    db.commit()
    
    return {"audio_id": audio_id, "file_path": file_path}

@router.post("/sync/batch", response_model=SyncStatusResponse)
async def batch_sync_responses(
    sync_request: BatchSyncRequest,
    db: Session = Depends(get_db)
):
    """Batch sync multiple responses from mobile app"""
    synced_count = 0
    failed_count = 0
    errors = []
    
    for response_data in sync_request.responses:
        try:
            # Check if response already exists
            existing = db.query(ResponseDB).filter(ResponseDB.id == response_data.id).first()
            
            if existing:
                # Update existing response
                encrypted_responses = privacy_service.encrypt_sensitive_data(response_data.responses)
                existing.responses = encrypted_responses
                existing.is_synced = True
                db.commit()
            else:
                # Create new response
                encrypted_responses = privacy_service.encrypt_sensitive_data(response_data.responses)
                
                db_response = ResponseDB(
                    id=response_data.id,
                    survey_id=response_data.survey_id,
                    respondent_id=response_data.respondent_id,
                    responses=encrypted_responses,
                    location_lat=response_data.location.latitude if response_data.location else None,
                    location_lng=response_data.location.longitude if response_data.location else None,
                    device_info=response_data.device_info.dict() if response_data.device_info else None,
                    verification_data=response_data.verification_data.dict() if response_data.verification_data else None,
                    confidence_scores=response_data.confidence_scores,
                    is_complete=response_data.is_complete,
                    is_synced=True,
                    created_at=response_data.created_at or datetime.now()
                )
                
                db.add(db_response)
                db.commit()
            
            synced_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Response {response_data.id}: {str(e)}")
    
    return SyncStatusResponse(
        total_responses=len(sync_request.responses),
        synced_responses=synced_count,
        failed_responses=failed_count,
        errors=errors
    )

@router.get("/export/csv/{survey_id}")
async def export_survey_csv(
    survey_id: str,
    anonymized: bool = True,
    db: Session = Depends(get_db)
):
    """Export survey responses as CSV"""
    responses = db.query(ResponseDB).filter(ResponseDB.survey_id == survey_id).all()
    
    if not responses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No responses found for this survey"
        )
    
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['response_id', 'created_at', 'is_complete', 'location_lat', 'location_lng']
    
    # Add dynamic headers from first response
    if responses:
        first_response_data = responses[0].responses
        if anonymized:
            first_response_data = privacy_service.anonymize_response(
                privacy_service.decrypt_sensitive_data(first_response_data)
            )
        else:
            first_response_data = privacy_service.decrypt_sensitive_data(first_response_data)
        
        headers.extend(first_response_data.keys())
    
    writer.writerow(headers)
    
    # Write data rows
    for response in responses:
        response_data = response.responses
        
        if anonymized:
            response_data = privacy_service.anonymize_response(
                privacy_service.decrypt_sensitive_data(response_data)
            )
        else:
            response_data = privacy_service.decrypt_sensitive_data(response_data)
        
        row = [
            response.id,
            response.created_at.isoformat() if response.created_at else '',
            response.is_complete,
            response.location_lat,
            response.location_lng
        ]
        
        # Add response data
        for key in headers[5:]:  # Skip the first 5 metadata columns
            row.append(response_data.get(key, ''))
        
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=survey_{survey_id}_responses.csv"}
    )

def _convert_db_to_model(db_response: ResponseDB) -> ResponseModel:
    """Convert database model to pydantic model"""
    # Decrypt sensitive data for API response
    decrypted_responses = privacy_service.decrypt_sensitive_data(db_response.responses)
    
    location = None
    if db_response.location_lat and db_response.location_lng:
        location = LocationData(
            latitude=db_response.location_lat,
            longitude=db_response.location_lng
        )
    
    device_info = None
    if db_response.device_info:
        device_info = DeviceInfo(**db_response.device_info)
    
    verification_data = None
    if db_response.verification_data:
        verification_data = VerificationData(**db_response.verification_data)
    
    return ResponseModel(
        id=db_response.id,
        survey_id=db_response.survey_id,
        respondent_id=db_response.respondent_id,
        responses=decrypted_responses,
        location=location,
        device_info=device_info,
        verification_data=verification_data,
        confidence_scores=db_response.confidence_scores,
        is_complete=db_response.is_complete,
        created_at=db_response.created_at
    )
