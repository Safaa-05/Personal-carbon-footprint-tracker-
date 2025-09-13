from fastapi import FastAPI, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List
from datetime import date, datetime
from sqlmodel import Session, select
from app import models, db, auth, utils
from pydantic import BaseModel
import json

app = FastAPI(title="Personal Carbon Footprint Tracker API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# init db when starting
@app.on_event("startup")
def on_startup():
    db.init_db()

# Pydantic schemas
class RegisterIn(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AnonymousPayload(BaseModel):
    electricity_kwh: float = 0.0
    renewable: bool = False
    cooking_fuel: str = "lpg"
    cooking_amount: float = 0.0
    transport_km: float = 0.0
    mode: str = "bus"
    fuel_type: Optional[str] = None
    fuel_consumption: Optional[float] = None
    days: int = 30
    food_type: str = "non_vegetarian"
    food_waste_kg: float = 0.0
    waste_kg: float = 0.0
    is_segregated: bool = False

class AuthenticatedPayload(AnonymousPayload):
    # logged-in has more options
    red_meat_freq_per_week: Optional[int] = None
    flights_per_year: Optional[int] = 0
    household_size: Optional[int] = 1

# helper to get current user
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(db.get_session)) -> models.User:
    token_data = auth.decode_access_token(token)
    if not token_data or not token_data.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = session.get(models.User, token_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Register
@app.post("/register", status_code=201)
def register(data: RegisterIn, session: Session = Depends(db.get_session)):
    q = select(models.User).where(models.User.email == data.email)
    existing = session.exec(q).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.hash_password(data.password)
    user = models.User(email=data.email, hashed_password=hashed, full_name=data.full_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "email": user.email}

# Token (login)
@app.post("/token", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(db.get_session)):
    q = select(models.User).where(models.User.email == form_data.username)
    user = session.exec(q).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token({"user_id": user.id})
    return {"access_token": token}

# 1) Anonymous monthly calculation (no storage)
@app.post("/calculate/anonymous")
def calculate_anonymous(payload: AnonymousPayload = Body(...)):
    # treat as month (30 days)
    data = payload.dict()
    calc = utils.calculate_total_from_payload({**data, "days": 30})
    # add suggestions (no previous)
    recs = utils.generate_recommendations(calc["total"], None)
    out = {"month": date.today().replace(day=1).isoformat(), "breakdown": calc, "recommendations": recs}
    return out

# 2) Authenticated calculation & store (monthly)
@app.post("/calculate", status_code=201)
def calculate_and_store(payload: AuthenticatedPayload = Body(...), user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    # payload.days used to scale; assume user sends month days or keep 30 if not provided
    data = payload.dict()
    calc = utils.calculate_total_from_payload(data)
    # decide month id: use first day of current month unless user supplies custom month param (extendable)
    month = date.today().replace(day=1)
    # check if a report for that month already exists (update or create)
    q = select(models.Report).where(models.Report.user_id == user.id, models.Report.month == month)
    existing = session.exec(q).first()
    raw_input = json.dumps(data)
    if existing:
        # update
        existing.electricity = calc["electricity"]
        existing.cooking = calc["cooking"]
        existing.transport = calc["transport"]
        existing.food = calc["food"]
        existing.waste = calc["waste"]
        existing.total = calc["total"]
        existing.raw_input = raw_input
        existing.created_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        report = existing
    else:
        report = models.Report(
            user_id=user.id,
            month=month,
            electricity=calc["electricity"],
            cooking=calc["cooking"],
            transport=calc["transport"],
            food=calc["food"],
            waste=calc["waste"],
            total=calc["total"],
            raw_input=raw_input
        )
        session.add(report)
        session.commit()
        session.refresh(report)
    # fetch previous month's total for recommendations
    previous_month = (month.replace(day=1).toordinal() - 1)  # not used directly
    # simpler: query for most recent prior month
    q2 = select(models.Report).where(models.Report.user_id == user.id, models.Report.month < month).order_by(models.Report.month.desc())
    prev = session.exec(q2).first()
    prev_total = prev.total if prev else None
    recs = utils.generate_recommendations(report.total, prev_total)
    return {
        "id": report.id,
        "month": report.month.isoformat(),
        "breakdown": {
            "electricity": report.electricity,
            "cooking": report.cooking,
            "transport": report.transport,
            "food": report.food,
            "waste": report.waste,
            "total": report.total
        },
        "recommendations": recs
    }

# 3) List user's reports (paginated simple)
@app.get("/reports")
def list_reports(user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    q = select(models.Report).where(models.Report.user_id == user.id).order_by(models.Report.month.desc())
    results = session.exec(q).all()
    out = []
    for r in results:
        out.append({
            "id": r.id,
            "month": r.month.isoformat(),
            "total": r.total,
            "electricity": r.electricity,
            "cooking": r.cooking,
            "transport": r.transport,
            "food": r.food,
            "waste": r.waste,
            "created_at": r.created_at.isoformat()
        })
    return out

# 4) Download report JSON or PDF
@app.get("/reports/{report_id}/download")
def download_report(report_id: int, as_pdf: bool = False, user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    report = session.get(models.Report, report_id)
    if not report or report.user_id != user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    meta = {
        "month": report.month.isoformat(),
        "electricity": report.electricity,
        "cooking": report.cooking,
        "transport": report.transport,
        "food": report.food,
        "waste": report.waste,
        "total": report.total,
        "recommendations": utils.generate_recommendations(report.total, None).get("recommendations", [])
    }
    if as_pdf:
        bytes_pdf = utils.generate_report_pdf(meta)
        return Response(content=bytes_pdf, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=carbon_report_{report.month.isoformat()}.pdf"
        })
    else:
        return meta

# 5) Graph data for comparisons (return a simple series by month)
@app.get("/reports/graph")
def reports_graph(user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    q = select(models.Report).where(models.Report.user_id == user.id).order_by(models.Report.month.asc())
    rows = session.exec(q).all()
    series = [{"month": r.month.isoformat(), "total": r.total} for r in rows]
    return {"series": series}

# 6) Summary: aggregated till now
@app.get("/summary")
def summary(user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    q = select(models.Report).where(models.Report.user_id == user.id).order_by(models.Report.month.asc())
    rows = session.exec(q).all()
    if not rows:
        return {"message": "No reports yet", "data": None}
    total_sum = sum(r.total for r in rows)
    avg = total_sum / len(rows)
    latest = rows[-1]
    # compare latest vs previous
    prev = rows[-2] if len(rows) >= 2 else None
    change = None
    if prev:
        change = round(latest.total - prev.total, 2)
    return {
        "months_recorded": len(rows),
        "total_sum": round(total_sum, 2),
        "average_per_month": round(avg, 2),
        "latest_month": latest.month.isoformat(),
        "latest_total": latest.total,
        "change_from_previous": change
    }

# 7) Get recommendations endpoint (for explicit requests)
@app.get("/recommendations")
def recommendations(user: models.User = Depends(get_current_user), session: Session = Depends(db.get_session)):
    # find latest and previous
    q = select(models.Report).where(models.Report.user_id == user.id).order_by(models.Report.month.desc())
    rows = session.exec(q).all()
    if not rows:
        return {"recommendations": ["No data. Create your first monthly report."], "message": "No data"}
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else None
    prev_total = prev.total if prev else None
    recs = utils.generate_recommendations(latest.total, prev_total)
    return recs
