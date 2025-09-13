# backend/utils/calculator.py
import json
from fastapi import HTTPException
from .anonymous_calculator import (
    calculate_electricity, calculate_cooking, calculate_transport,
    calculate_food, calculate_waste
)

with open("backend/utils/emission_factors.json") as f:
    FACTORS = json.load(f)

# ---------------- Guest Mode ----------------
def calculate_total(data: dict) -> dict:
    return {
        "electricity": round(calculate_electricity(data.get("electricity_kwh", 0), data.get("renewable", False)), 2),
        "cooking": round(calculate_cooking(data.get("cooking_fuel", "lpg"), data.get("cooking_amount", 0)), 2),
        "transport": round(calculate_transport(
            data.get("transport_km", 0),
            data.get("mode", "bus"),
            data.get("fuel_type"),
            data.get("fuel_consumption")
        ), 2),
        "food": round(calculate_food(
            data.get("days", 30),
            data.get("food_type", "non_vegetarian"),
            data.get("food_waste_kg", 0)
        ), 2),
        "waste": round(calculate_waste(data.get("waste_kg", 0), data.get("is_segregated", False)), 2),
    }

# ---------------- Logged-in Mode ----------------
def calculate_logged(data: dict) -> dict:
    try:
        electricity = data["electricity_kwh"] * (FACTORS["energy"]["renewable"] if data["renewable"] else FACTORS["energy"]["electricity"])
        cooking = data["cooking_amount"] * FACTORS["cooking"][data["cooking_fuel"]]

        # transport
        transport = 0
        if data["mode"] in ["car", "bike"]:
            fuel_used = data["distance_km"] * (data["fuel_consumption"] / 100)
            transport += fuel_used * FACTORS["fuels"][data["fuel_type"]]
        else:
            transport += data["distance_km"] * FACTORS["transport"][data["mode"]]

        # flights
        flights = data.get("flights_per_year", 0) * FACTORS["transport"]["flight"]

        # food
        baseline = FACTORS["food"]["diet_baseline"][data["diet_type"]] * (data.get("days", 30) / 365)
        red_meat = data.get("red_meat_freq", 0) * FACTORS["food"]["red_meat"]
        food_waste = data.get("food_waste_kg", 0) * FACTORS["food"]["waste"]
        food = baseline + red_meat + food_waste

        # waste
        disposal_method = data.get("waste_disposal", "landfill")
        waste_total = data["waste_kg"] * FACTORS["waste"][disposal_method]

        total = electricity + cooking + transport + flights + food + waste_total
        return {
            "electricity": round(electricity, 2),
            "cooking": round(cooking, 2),
            "transport": round(transport + flights, 2),
            "food": round(food, 2),
            "waste": round(waste_total, 2),
            "total": round(total, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
