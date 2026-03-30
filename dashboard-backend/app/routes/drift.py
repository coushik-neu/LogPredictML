from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()

@router.get("/drift-status")
def drift_status(db: Session = Depends(get_db)):
    row = db.execute(text("SELECT drift_detected, drift_score FROM drift_status LIMIT 1")).fetchone()

    return {
        "drift_detected": row[0],
        "drift_score": float(row[1])
    }