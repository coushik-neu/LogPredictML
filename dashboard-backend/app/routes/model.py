from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import get_model_health

router = APIRouter()

@router.get("/model-health")
def model_health(db: Session = Depends(get_db)):
    return get_model_health(db)