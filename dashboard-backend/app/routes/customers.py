from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.churn_service import get_churn_distribution, get_high_risk_customers

router = APIRouter()

@router.get("/churn-distribution")
def churn_distribution(db: Session = Depends(get_db)):
    return get_churn_distribution(db)

@router.get("/high-risk-customers")
def high_risk(db: Session = Depends(get_db)):
    return get_high_risk_customers(db)