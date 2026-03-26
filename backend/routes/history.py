from fastapi import APIRouter
from services.history_service import get_recent_reviews
from models.schemas import HistoryItem

router = APIRouter()

@router.get("/history", response_model=list[HistoryItem])
def get_history():
    return get_recent_reviews(limit=5)
