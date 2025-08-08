from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.survey import SurveyModel, SurveyCreateRequest, SurveyUpdateRequest, SurveyDB
from ..database import get_db
import uuid
import yaml
import json

router = APIRouter()

@router.get("/surveys", response_model=List[SurveyModel])
async def get_surveys(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of all surveys"""
    query = db.query(SurveyDB)
    
    if active_only:
        query = query.filter(SurveyDB.is_active == True)
    
    surveys = query.offset(skip).limit(limit).all()
    
    return [_convert_db_to_model(survey) for survey in surveys]

@router.get("/surveys/{survey_id}", response_model=SurveyModel)
async def get_survey(survey_id: str, db: Session = Depends(get_db)):
    """Get specific survey by ID"""
    survey = db.query(SurveyDB).filter(SurveyDB.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    return _convert_db_to_model(survey)

@router.post("/surveys", response_model=SurveyModel, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_request: SurveyCreateRequest,
    db: Session = Depends(get_db)
):
    """Create new survey"""
    survey_id = str(uuid.uuid4())
    
    # Convert pydantic model to dictionary for JSON storage
    definition = {
        "questions": [q.dict() for q in survey_request.questions],
        "logic": survey_request.logic.dict() if survey_request.logic else {},
        "responses": survey_request.responses.dict() if survey_request.responses else {}
    }
    
    db_survey = SurveyDB(
        id=survey_id,
        title=survey_request.title,
        description=survey_request.description,
        definition=definition,
        languages=survey_request.languages
    )
    
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    
    return _convert_db_to_model(db_survey)

@router.put("/surveys/{survey_id}", response_model=SurveyModel)
async def update_survey(
    survey_id: str,
    survey_request: SurveyUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update existing survey"""
    survey = db.query(SurveyDB).filter(SurveyDB.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Update fields
    if survey_request.title:
        survey.title = survey_request.title
    if survey_request.description is not None:
        survey.description = survey_request.description
    if survey_request.languages:
        survey.languages = survey_request.languages
    if survey_request.is_active is not None:
        survey.is_active = survey_request.is_active
    
    # Update definition if questions provided
    if survey_request.questions or survey_request.logic or survey_request.responses:
        definition = survey.definition.copy()
        
        if survey_request.questions:
            definition["questions"] = [q.dict() for q in survey_request.questions]
        if survey_request.logic:
            definition["logic"] = survey_request.logic.dict()
        if survey_request.responses:
            definition["responses"] = survey_request.responses.dict()
        
        survey.definition = definition
    
    db.commit()
    db.refresh(survey)
    
    return _convert_db_to_model(survey)

@router.delete("/surveys/{survey_id}")
async def delete_survey(survey_id: str, db: Session = Depends(get_db)):
    """Delete survey (soft delete by setting inactive)"""
    survey = db.query(SurveyDB).filter(SurveyDB.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    survey.is_active = False
    db.commit()
    
    return {"message": "Survey deleted successfully"}

@router.post("/surveys/upload-yaml")
async def upload_survey_yaml(
    yaml_content: str,
    db: Session = Depends(get_db)
):
    """Upload survey definition from YAML"""
    try:
        # Parse YAML content
        data = yaml.safe_load(yaml_content)
        survey_model = SurveyModel.from_yaml(yaml_content)
        
        # Check if survey already exists
        existing_survey = db.query(SurveyDB).filter(SurveyDB.id == survey_model.id).first()
        
        if existing_survey:
            # Update existing survey
            existing_survey.title = survey_model.title
            existing_survey.definition = data
            existing_survey.languages = survey_model.languages
            existing_survey.version = existing_survey.version + 1
            db.commit()
            db.refresh(existing_survey)
            return _convert_db_to_model(existing_survey)
        else:
            # Create new survey
            db_survey = SurveyDB(
                id=survey_model.id,
                title=survey_model.title,
                definition=data,
                languages=survey_model.languages
            )
            db.add(db_survey)
            db.commit()
            db.refresh(db_survey)
            return _convert_db_to_model(db_survey)
            
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing survey: {str(e)}"
        )

def _convert_db_to_model(db_survey: SurveyDB) -> SurveyModel:
    """Convert database model to pydantic model"""
    definition = db_survey.definition
    
    questions = [Question(**q) for q in definition.get("questions", [])]
    logic = SurveyLogic(**definition.get("logic", {}))
    responses = SurveyResponses(**definition.get("responses", {}))
    
    return SurveyModel(
        id=db_survey.id,
        title=db_survey.title,
        version=db_survey.version,
        languages=db_survey.languages or [],
        questions=questions,
        logic=logic,
        responses=responses
    )
