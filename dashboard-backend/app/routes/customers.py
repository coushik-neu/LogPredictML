from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.churn_service import get_churn_distribution, get_high_risk_customers
from app.services.customer_service import get_high_risk_customers, get_customer_orders, get_customer_revenue_trend, get_customer_summary

router = APIRouter()

@router.get("/churn-distribution")
def churn_distribution(db: Session = Depends(get_db)):
    return get_churn_distribution(db)

@router.get("/high-risk-customers")
def high_risk(
    type: str = Query("risk", pattern="^(risk|active)$"),  
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    return get_high_risk_customers(
        db=db,
        type=type,           
        page=page,
        page_size=page_size
    )


@router.get("/customer-orders/{customer_id}")
def customer_orders(customer_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return get_customer_orders(db, customer_id, limit)


@router.get("/customer-summary/{customer_id}")
def customer_summary(customer_id: int, db: Session = Depends(get_db)):
    return get_customer_summary(db, customer_id)


@router.get("/customer-revenue-trend/{customer_id}")
def customer_revenue(customer_id: int, db: Session = Depends(get_db)):
    return get_customer_revenue_trend(db, customer_id)
