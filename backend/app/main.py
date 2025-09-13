from fastapi import FastAPI
from app.api.routes_auth import router as auth_router
from app.api.routes_calculate import router as calculate_router
from app.api.routes_reports import router as reports_router
from app.api.routes_recommendations import router as recommend_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(calculate_router, prefix="/calculate")
app.include_router(reports_router, prefix="/reports")
app.include_router(recommend_router, prefix="/recommend")
