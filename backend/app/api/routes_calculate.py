import json
from fastapi import HTTPException
from fastapi import APIRouter, Depends
from app.schemas.report import AnonymousInput, AuthInput
from app.services.calculation import calculate_total
from app.models.user import User
from app.database.session import SessionLocal
from app.models.report import CarbonReport
from sqlalchemy.orm import Session
from app.api.routes_auth import oauth2_scheme, get_user
from jose import jwt
from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    user = get_user(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/anonymous")
def calc_anonymous(data: AnonymousInput):
    res = calculate_total(data.dict())
    return res

@router.post("/authenticated")
def calc_authenticated(
    data: AuthInput, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report_data = data.dict()
    res = calculate_total(report_data, authenticated=True)
    from datetime import datetime
    now = datetime.utcnow()
    period = now.strftime("%Y-%m")
    report = CarbonReport(
        user_id=user.id, period=period,
        electricity=res["electricity"], 
        cooking=res["cooking"],
        transport=res["transport"],
        food=res["food"],
        waste=res["waste"],
        total=res["total"],
        data_json=json.dumps(report_data),
        created_at=now
    )
    db.add(report)
    db.commit()
    return res
