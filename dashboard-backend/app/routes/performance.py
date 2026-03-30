from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import get_performance_trend, get_model_performance_trend

router = APIRouter()

@router.get("/performance-trend")
def performance_trend(db: Session = Depends(get_db)):
    return get_model_performance_trend(db)

