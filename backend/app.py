from fastapi import FastAPI
from pydantic import BaseModel
from utils.calculator import calculate_total

app = FastAPI()

class UserInput(BaseModel):
    transport_km: float
    mode: str
    energy_kwh: float
    days: int
    food_type: str
    waste_kg: float

@app.post("/calculate")
def calculate(data: UserInput):
    result = calculate_total(data.dict())
    return result
