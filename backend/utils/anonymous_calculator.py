# backend/utils/anonymous_calculator.py
import json

with open( '../emission_factors.json' ) as f:
    FACTORS = json.load(f)

def calculate_electricity(kwh: float, renewable: bool) -> float:
    factor = FACTORS["energy"]["renewable"] if renewable else FACTORS["energy"]["electricity"]
    return kwh * factor

def calculate_cooking(fuel: str, amount: float) -> float:
    return amount * FACTORS["cooking"].get(fuel, 0)

def calculate_transport(distance_km: float, mode: str, fuel_type: str = None, fuel_consumption: float = None) -> float:
    if mode in ["car", "bike"] and fuel_type and fuel_consumption:
        fuel_used = distance_km * (fuel_consumption / 100)
        return fuel_used * FACTORS["fuels"].get(fuel_type, 0)
    return distance_km * FACTORS["transport"].get(mode, 0)

def calculate_food(days: int, diet_type: str, food_waste_kg: float = 0) -> float:
    baseline = FACTORS["food"]["diet_baseline"].get(diet_type, 0)
    return (days / 30) * baseline + food_waste_kg * FACTORS["food"]["waste"]

def calculate_waste(kg: float, is_segregated: bool) -> float:
    factor = FACTORS["waste"]["recycle"] if is_segregated else FACTORS["waste"]["landfill"]
    return kg * factor
