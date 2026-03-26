from fastapi import APIRouter, HTTPException
from models.schemas import ReviewRequest, ReviewResult
from services.ai_service import analyze_code
from services.history_service import save_review

router = APIRouter()

@router.post("/review", response_model=ReviewResult)
async def review_code(request: ReviewRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    if len(request.code) > 20000:
        raise HTTPException(status_code=400, detail="Code too long (max 20,000 chars)")

    result = await analyze_code(request.code, request.language)

    save_review(
        language=request.language,
        code=request.code,
        result=result.model_dump()
    )

    return result
