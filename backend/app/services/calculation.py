import json
from fastapi import HTTPException

with open("app/emission_factors/emission_factors.json") as f:
    FACTORS = json.load(f)

def calculate_electricity(kwh: float, renewable: bool = False) -> float:
    factor = FACTORS["energy"]["renewable"] if renewable else FACTORS["energy"]["electricity"]
    return kwh * factor

def calculate_cooking(fuel_type: str, amount: float) -> float:
    if fuel_type not in FACTORS["cooking"]:
        raise HTTPException(status_code=400, detail=f"Invalid cooking fuel type: {fuel_type}")
    return amount * FACTORS["cooking"][fuel_type]

def calculate_transport(distance_km: float, mode: str, fuel_type: str = None, fuel_consumption: float = None, 
                       public_transports: int = 0, flights_per_year: int = 0) -> float:
    base = 0
    if mode in FACTORS["transport"]:
        base += distance_km * FACTORS["transport"][mode]
    elif mode in ["car", "bike"]:
        if not fuel_type or fuel_type not in FACTORS["fuels"]:
            raise HTTPException(status_code=400, detail=f"Invalid or missing fuel type: {fuel_type}")
        if not fuel_consumption:
            raise HTTPException(status_code=400, detail="Fuel consumption required for car/bike")
        fuel_used = distance_km * (fuel_consumption / 100)
        base += fuel_used * FACTORS["fuels"][fuel_type]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid transport mode: {mode}")
    if public_transports:
        base += public_transports * FACTORS["transport"]["bus"] * 10
    if flights_per_year:
        base += flights_per_year * FACTORS["transport"]["flight"]
    return base

def calculate_food(days: int, diet_type: str, waste_kg: float = 0, red_meat_freq: int = 0, food_quantity: float = 1) -> float:
    if diet_type not in FACTORS["food"]["diet_baseline"]:
        raise HTTPException(status_code=400, detail=f"Invalid diet type: {diet_type}")
    baseline = FACTORS["food"]["diet_baseline"][diet_type] * (days / 365)
    waste = waste_kg * FACTORS["food"]["waste"]
    meat = red_meat_freq * FACTORS["food"].get("red_meat", 0)
    quantity = food_quantity * FACTORS["food"].get("food_quantity", 1)
    return baseline + waste + meat + quantity

def calculate_waste(kg: float, segregated: bool = False, method: str = None) -> float:
    if method and method in FACTORS["waste"]:
        factor = FACTORS["waste"][method]
    else:
        factor = FACTORS["waste"]["segregated"] if segregated else FACTORS["waste"]["landfill"]
    return kg * factor

def calculate_total(data: dict, authenticated: bool = False) -> dict:
    electricity = calculate_electricity(data.get("electricity_kwh", 0), data.get("renewable", False))
    cooking = calculate_cooking(data.get("cooking_fuel", "lpg"), data.get("cooking_amount", 0))
    transport = calculate_transport(
        data.get("transport_km", 0),
        data.get("mode", "bus"),
        data.get("fuel_type"),
        data.get("fuel_consumption"),
        data.get("public_transports", 0),
        data.get("flights_per_year", 0)
    )
    food = calculate_food(
        data.get("days", 30),
        data.get("food_type", "non_vegetarian"),
        data.get("food_waste_kg", 0),
        data.get("red_meat_freq", 0),
        data.get("food_quantity", 1)
    )
    waste = calculate_waste(
        data.get("waste_kg", 0),
        data.get("is_segregated", False),
        data.get("waste_method")
    )
    total = electricity + cooking + transport + food + waste
    return {
        "electricity": round(electricity, 2),
        "cooking": round(cooking, 2),
        "transport": round(transport, 2),
        "food": round(food, 2),
        "waste": round(waste, 2),
        "total": round(total, 2)
    }
