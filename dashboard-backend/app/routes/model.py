from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import get_model_health, get_current_model, get_all_models

router = APIRouter()

@router.get("/model-health")
def model_health(db: Session = Depends(get_db)):
    return get_model_health(db)

@router.get("/model-health")
def model_health(db: Session = Depends(get_db)):
    return get_current_model(db)


# ----------------------------------------
# ALL MODELS
# ----------------------------------------
@router.get("/models")
def models(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    return get_all_models(db, page, page_size)