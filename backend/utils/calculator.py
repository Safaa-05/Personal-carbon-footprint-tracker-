import json
from fastapi import HTTPException

# Load emission factors
with open("data/emission_factors.json") as f:
    FACTORS = json.load(f)

def calculate_electricity(kwh: float, renewable: bool = False) -> float:
    factor = FACTORS["energy"]["renewable"] if renewable else FACTORS["energy"]["electricity"]
    return kwh * factor

def calculate_cooking(fuel_type: str, amount: float) -> float:
    if fuel_type not in FACTORS["cooking"]:
        raise HTTPException(status_code=400, detail=f"Invalid cooking fuel type: {fuel_type}")
    return amount * FACTORS["cooking"][fuel_type]

def calculate_transport(distance_km: float, mode: str, fuel_type: str = None, fuel_consumption: float = None) -> float:
    if mode in FACTORS["transport"]:
        return distance_km * FACTORS["transport"][mode]
    elif mode in ["car", "bike"]:
        if not fuel_type or fuel_type not in FACTORS["fuels"]:
            raise HTTPException(status_code=400, detail=f"Invalid or missing fuel type: {fuel_type}")
        if not fuel_consumption:
            raise HTTPException(status_code=400, detail="Fuel consumption required for car/bike")
        fuel_used = distance_km * (fuel_consumption / 100)
        return fuel_used * FACTORS["fuels"][fuel_type]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid transport mode: {mode}")

def calculate_food(days: int, diet_type: str, waste_kg: float = 0) -> float:
    if diet_type not in FACTORS["food"]["diet_baseline"]:
        raise HTTPException(status_code=400, detail=f"Invalid diet type: {diet_type}")
    baseline = FACTORS["food"]["diet_baseline"][diet_type] * (days / 365)  # per year → scaled to days
    waste = waste_kg * FACTORS["food"]["waste"]
    return baseline + waste

def calculate_waste(kg: float, segregated: bool = False) -> float:
    factor = FACTORS["waste"]["segregated"] if segregated else FACTORS["waste"]["landfill"]
    return kg * factor

def calculate_total(data: dict) -> dict:
    electricity = calculate_electricity(data.get("electricity_kwh", 0), data.get("renewable", False))
    cooking = calculate_cooking(data.get("cooking_fuel", "lpg"), data.get("cooking_amount", 0))
    transport = calculate_transport(
        data.get("transport_km", 0),
        data.get("mode", "bus"),
        data.get("fuel_type"),
        data.get("fuel_consumption")
    )
    food = calculate_food(data.get("days", 30), data.get("food_type", "non_vegetarian"), data.get("food_waste_kg", 0))
    waste = calculate_waste(data.get("waste_kg", 0), data.get("is_segregated", False))

    total = electricity + cooking + transport + food + waste

    return {
        "electricity": round(electricity, 2),
        "cooking": round(cooking, 2),
        "transport": round(transport, 2),
        "food": round(food, 2),
        "waste": round(waste, 2),
        "total": round(total, 2)
    }
