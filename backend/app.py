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

