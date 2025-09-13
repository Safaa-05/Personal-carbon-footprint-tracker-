from pydantic import BaseModel
from typing import Optional

class AnonymousInput(BaseModel):
    electricity_kwh: float
    renewable: bool
    cooking_fuel: str
    cooking_amount: float
    transport_km: float
    mode: str
    fuel_type: Optional[str]
    fuel_consumption: Optional[float]
    days: int = 30
    food_type: str
    food_waste_kg: float
    waste_kg: float
    is_segregated: bool

class AuthInput(BaseModel):
    electricity_kwh: float
    renewable: bool
    cooking_fuel: str
    cooking_amount: float
    transport_km: float
    mode: str
    vehicle_type: Optional[str]
    fuel_type: Optional[str]
    fuel_consumption: Optional[float]
    public_transports: Optional[int]
    flights_per_year: Optional[int]
    days: int = 30
    food_type: str
    red_meat_freq: Optional[int]
    food_quantity: Optional[float]
    food_waste_kg: float
    household_size: int
    waste_method: Optional[str]
    waste_kg: float
