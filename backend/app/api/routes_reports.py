from fastapi import APIRouter, Depends, HTTPException
from app.models.report import CarbonReport
from app.database.session import SessionLocal
from sqlalchemy.orm import Session
from app.api.routes_calculate import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_reports(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(CarbonReport).filter(CarbonReport.user_id == user.id).order_by(CarbonReport.period).all()
    return [
        {"period": r.period, "total": r.total, "id": r.id} for r in reports
    ]

@router.get("/{report_id}")
def download_report(report_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(CarbonReport).filter(CarbonReport.id == report_id, CarbonReport.user_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "period": report.period,
        "electricity": report.electricity,
        "cooking": report.cooking,
        "transport": report.transport,
        "food": report.food,
        "waste": report.waste,
        "total": report.total,
        "data": report.data_json,
        "created_at": report.created_at
    }

@router.get("/summary")
def summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(CarbonReport).filter(CarbonReport.user_id == user.id).all()
    if not reports:
        return {"msg": "No reports found"}
    all_totals = [r.total for r in reports]
    summary = {
        "average": round(sum(all_totals) / len(all_totals), 2),
        "highest": max(all_totals),
        "lowest": min(all_totals),
        "total_periods": len(reports)
    }
    return summary

@router.get("/trend")
def trend_data(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(CarbonReport).filter(CarbonReport.user_id == user.id).order_by(CarbonReport.period).all()
    return [
        {"period": r.period, "total": r.total} for r in reports
    ]
