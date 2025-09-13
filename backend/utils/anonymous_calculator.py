# backend/utils/anonymous_calculator.py

def calculate_electricity(kwh: float, renewable: bool) -> float:
    return kwh * (0.1 if renewable else 0.5)

def calculate_cooking(fuel: str, amount: float) -> float:
    factors = {"lpg": 2.9, "electric": 1.5, "wood": 4.5}
    return amount * factors.get(fuel, 3.0)

def calculate_transport(distance: float, mode: str, fuel_type: str = None, fuel_consumption: float = None) -> float:
    factors = {"bus": 0.05, "train": 0.03, "car": 0.2, "bike": 0.1, "flight": 0.15}
    if mode in ["car", "bike"] and fuel_consumption and fuel_type:
        fuel_factors = {"petrol": 2.3, "diesel": 2.7}
        fuel_used = distance * (fuel_consumption / 100)
        return fuel_used * fuel_factors.get(fuel_type, 2.5)
    return distance * factors.get(mode, 0.1)

def calculate_food(days: int, food_type: str, waste_kg: float = 0) -> float:
    diet_factors = {"vegetarian": 2.0, "non_vegetarian": 5.0, "mixed": 3.5}
    waste_factor = 1.0
    return days * diet_factors.get(food_type, 3.0) + waste_kg * waste_factor

def calculate_waste(waste_kg: float, segregated: bool) -> float:
    return waste_kg * (0.5 if segregated else 1.0)
