from fastapi import FastAPI
from pydantic import BaseModel
from utils.calculator import calculate_total

app = FastAPI()

# Define input model
class UserInput(BaseModel):
    transport_km: float
    mode: str
    energy_kwh: float
    days: int
    food_type: str
    waste_kg: float

@app.get("/")
def read_root():
    return {"message": "Carbon Footprint API is running"}

@app.post("/calculate")
def calculate(input: UserInput):
    # Convert Pydantic object to dict and pass to calculator
    result = calculate_total(input.dict())
    return result

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, allow all; later restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from utils.calculator import calculate_total
# backend/app.py
from fastapi import FastAPI
from auth import auth_router
from utils.calculator import calculate_total
from pydantic import BaseModel

app = FastAPI()

# include auth routes
app.include_router(auth_router)

class InputData(BaseModel):
    transport_km: float
    mode: str
    energy_kwh: float
    days: int
    food_type: str
    waste_kg: float

@app.post("/calculate")
def calculate(data: InputData):
    return calculate_total(data.dict())
