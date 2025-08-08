from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

Base = declarative_base()

class SurveyDB(Base):
    __tablename__ = "surveys"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    definition = Column(JSON, nullable=False)  # Store YAML as JSON
    version = Column(Integer, default=1)
    languages = Column(JSON)  # List of supported languages
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class QuestionDB(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, index=True)
    survey_id = Column(String, nullable=False)
    question_type = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    required = Column(Boolean, default=True)
    extract_config = Column(JSON)  # NLP extraction configuration
    conditions = Column(JSON)  # Conditional logic
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic models for API
class Question(BaseModel):
    id: str
    type: str
    text: str
    required: bool = True
    extract: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    retry_prompts: Optional[List[str]] = None
    follow_ups: Optional[List[Dict[str, Any]]] = None
    next: Optional[str] = None

class SurveyLogic(BaseModel):
    max_retries: int = 3
    confidence_threshold: float = 0.7
    auto_skip_timeout: int = 30

class SurveyResponses(BaseModel):
    thank_you: str
    error_generic: str
    error_unclear: str

class SurveyModel(BaseModel):
    id: str
    title: str
    version: float
    languages: List[str]
    questions: List[Question]
    logic: SurveyLogic
    responses: SurveyResponses
    
    @classmethod
    def from_yaml(cls, yaml_content: str):
        """Create survey model from YAML content"""
        import yaml
        data = yaml.safe_load(yaml_content)
        
        survey_data = data['survey']
        questions_data = data['questions']
        logic_data = data.get('logic', {})
        responses_data = data.get('responses', {})
        
        questions = [Question(**q) for q in questions_data]
        logic = SurveyLogic(**logic_data)
        responses = SurveyResponses(**responses_data)
        
        return cls(
            id=survey_data['id'],
            title=survey_data['title'],
            version=survey_data['version'],
            languages=survey_data['languages'],
            questions=questions,
            logic=logic,
            responses=responses
        )

class SurveyCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    languages: List[str]
    questions: List[Question]
    logic: Optional[SurveyLogic] = None
    responses: Optional[SurveyResponses] = None

class SurveyUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    languages: Optional[List[str]] = None
    questions: Optional[List[Question]] = None
    logic: Optional[SurveyLogic] = None
    responses: Optional[SurveyResponses] = None
    is_active: Optional[bool] = None
