from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ReviewRequest(BaseModel):
    code: str
    language: str

class Issue(BaseModel):
    title: str
    severity: str  # low | medium | high
    explanation: str
    suggested_fix: str
    line_number: Optional[int] = None

class ReviewResult(BaseModel):
    issues: List[Issue]
    overall_quality: str
    summary: str
    improved_code: str
    mode: str  # "ai" or "mock"

class HistoryItem(BaseModel):
    id: int
    language: str
    code_preview: str
    summary: str
    created_at: str
