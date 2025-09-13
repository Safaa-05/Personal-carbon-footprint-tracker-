from fastapi import APIRouter, Depends
from app.models.report import CarbonReport
from app.database.session import SessionLocal
from sqlalchemy.orm import Session
from app.api.routes_calculate import get_current_user
from app.services.recommendations import get_recommendation

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def recommend(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(CarbonReport).filter(CarbonReport.user_id == user.id).order_by(CarbonReport.period).all()
    if not reports or len(reports) < 2:
        return {"recommendation": "Keep tracking your carbon footprint for insights."}
    last = reports[-1].total
    prev = reports[-2].total
    return {"recommendation": get_recommendation(last, prev)}
