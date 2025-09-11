import json

# Load emission factors
with open("data/emission_factors.json") as f:
    FACTORS = json.load(f)

def calculate_transport(distance_km: float, mode: str) -> float:
    return distance_km * FACTORS["transport"].get(mode, 0)

def calculate_energy(kwh: float) -> float:
    return kwh * FACTORS["energy"]["electricity"]

def calculate_food(days: int, diet_type: str) -> float:
    return days * FACTORS["food"].get(diet_type, 0)

def calculate_waste(kg: float) -> float:
    return kg * FACTORS["waste"]["general"]

def calculate_total(data: dict) -> dict:
    transport = calculate_transport(data["transport_km"], data["mode"])
    energy = calculate_energy(data["energy_kwh"])
    food = calculate_food(data["days"], data["food_type"])
    waste = calculate_waste(data["waste_kg"])
    
    total = transport + energy + food + waste
    return {
        "transport": transport,
        "energy": energy,
        "food": food,
        "waste": waste,
        "total": total
    }
from fastapi import HTTPException

def calculate_transport(distance_km: float, mode: str) -> float:
    if mode not in FACTORS["transport"]:
        raise HTTPException(status_code=400, detail=f"Invalid transport mode: {mode}")
    return distance_km * FACTORS["transport"][mode]
