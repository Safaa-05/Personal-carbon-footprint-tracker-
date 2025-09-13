import json
import os

# Path to the JSON file
EMISSION_FACTORS_FILE = os.path.join(os.path.dirname(__file__), "emission_factors.json")

def load_emission_factors():
    """Load emission factors from JSON file."""
    with open(EMISSION_FACTORS_FILE, "r") as f:
        return json.load(f)

def calculate_emission(category: str, subcategory: str, amount: float) -> float:
    """
    Calculate carbon emissions.

    Args:
        category (str): Main category (e.g., 'transport', 'energy', 'food', 'waste')
        subcategory (str): Subcategory inside the category (e.g., 'car_petrol', 'electricity', 'beef')
        amount (float): Activity data (e.g., km travelled, kWh used, kg consumed)

    Returns:
        float: Estimated CO₂e emissions (kg)
    """
    factors = load_emission_factors()
    
    try:
        factor = factors[category][subcategory]
    except KeyError:
        raise ValueError(f"Emission factor not found for {category} -> {subcategory}")
    
    return round(amount * factor, 2)

# Example usage
if __name__ == "__main__":
    # Example: 100 km by petrol car
    print("Car Petrol (100 km):", calculate_emission("transport", "car_petrol", 100), "kg CO₂e")

    # Example: 50 kWh of electricity
    print("Electricity (50 kWh):", calculate_emission("energy", "electricity", 50), "kg CO₂e")

    # Example: 2 kg of beef
    print("Beef (2 kg):", calculate_emission("food", "beef", 2), "kg CO₂e")
