from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.business_service import (
    get_total_revenue,
    get_orders_today,
    get_top_industries,
    get_top_products,
    get_revenue_trend
)

router = APIRouter()

@router.get("/total-revenue")
def total_revenue(db: Session = Depends(get_db)):
    return get_total_revenue(db)

@router.get("/orders-today")
def orders_today(db: Session = Depends(get_db)):
    return get_orders_today(db)

@router.get("/top-industries")
def top_industries(db: Session = Depends(get_db)):
    return get_top_industries(db)

@router.get("/top-products")
def top_products(db: Session = Depends(get_db)):
    return get_top_products(db)

@router.get("/revenue-trend")
def revenue_trend(db: Session = Depends(get_db)):
    return get_revenue_trend(db)