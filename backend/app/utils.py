import json
from fastapi import HTTPException
from datetime import date, datetime
from typing import Dict, Any, Optional
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.models import Report
import os

# Load emission factors once
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emission_factors.json")
with open(DATA_PATH) as f:
    FACTORS = json.load(f)


# Calculation functions
def calculate_electricity(kwh: float, renewable: bool = False) -> float:
    factor = FACTORS["energy"]["renewable"] if renewable else FACTORS["energy"]["electricity"]
    return kwh * factor

def calculate_cooking(fuel_type: str, amount: float) -> float:
    if fuel_type not in FACTORS["cooking"]:
        raise HTTPException(status_code=400, detail=f"Invalid cooking fuel type: {fuel_type}")
    return amount * FACTORS["cooking"][fuel_type]

def calculate_transport(distance_km: float, mode: str, fuel_type: Optional[str] = None, fuel_consumption: Optional[float] = None) -> float:
    # mode keyed transport per-km
    if mode in FACTORS["transport"]:
        # for flight, user may pass 'flight' and we may want to use flight_per_km
        if mode == "flight":
            return distance_km * FACTORS["transport"]["flight_per_km"]
        return distance_km * FACTORS["transport"][mode]
    elif mode in ["car", "bike"]:
        if not fuel_type or fuel_type not in FACTORS["fuels"]:
            raise HTTPException(status_code=400, detail=f"Invalid or missing fuel type: {fuel_type}")
        if not fuel_consumption:
            raise HTTPException(status_code=400, detail="Fuel consumption (L/100km) required for car/bike")
        fuel_used_liters = distance_km * (fuel_consumption / 100.0)
        return fuel_used_liters * FACTORS["fuels"][fuel_type]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid transport mode: {mode}")

def calculate_food(days: int, diet_type: str, waste_kg: float = 0, red_meat_freq_per_week: Optional[int] = None) -> float:
    if diet_type not in FACTORS["food"]["diet_baseline"]:
        raise HTTPException(status_code=400, detail=f"Invalid diet type: {diet_type}")
    baseline = FACTORS["food"]["diet_baseline"][diet_type] * (days / 365.0)
    # optionally penalize red meat frequency
    extra = 0.0
    if red_meat_freq_per_week:
        # simplistic extra factor per instance per week scaled to days
        extra_per_year = red_meat_freq_per_week * 52 * 0.5  # 0.5 kgCO2e per red-meat meal (example)
        extra = extra_per_year * (days / 365.0)
    waste = waste_kg * FACTORS["food"]["waste"]
    return baseline + extra + waste

def calculate_waste(kg: float, segregated: bool = False) -> float:
    factor = FACTORS["waste"]["segregated"] if segregated else FACTORS["waste"]["landfill"]
    return kg * factor

def calculate_total_from_payload(payload: Dict[str, Any]) -> Dict[str, float]:
    electricity = calculate_electricity(payload.get("electricity_kwh", 0.0), payload.get("renewable", False))
    cooking = calculate_cooking(payload.get("cooking_fuel", "lpg"), payload.get("cooking_amount", 0.0))
    transport = calculate_transport(
        payload.get("transport_km", 0.0),
        payload.get("mode", "bus"),
        payload.get("fuel_type"),
        payload.get("fuel_consumption")
    )
    food = calculate_food(
        payload.get("days", 30),
        payload.get("food_type", "non_vegetarian"),
        payload.get("food_waste_kg", 0.0),
        payload.get("red_meat_freq_per_week")
    )
    waste = calculate_waste(payload.get("waste_kg", 0.0), payload.get("is_segregated", False))
    total = electricity + cooking + transport + food + waste
    return {
        "electricity": round(electricity, 2),
        "cooking": round(cooking, 2),
        "transport": round(transport, 2),
        "food": round(food, 2),
        "waste": round(waste, 2),
        "total": round(total, 2)
    }

# PDF generator for a report (returns bytes)
def generate_report_pdf(report_meta: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    title = "Carbon Footprint Report"
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, title)
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Date: {datetime.utcnow().isoformat()}")
    # report_meta expected to contain month, breakdown, total, suggestions
    y = height - 100
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Month: {report_meta.get('month')}")
    y -= 20
    c.setFont("Helvetica", 11)
    for k in ["electricity", "cooking", "transport", "food", "waste", "total"]:
        val = report_meta.get(k, "N/A")
        c.drawString(40, y, f"{k.capitalize()}: {val} kgCO2e")
        y -= 16
    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Recommendations:")
    y -= 16
    c.setFont("Helvetica", 10)
    recommendations = report_meta.get("recommendations", [])
    if not recommendations:
        c.drawString(40, y, "No specific recommendations.")
        y -= 16
    else:
        for r in recommendations:
            c.drawString(40, y, f"- {r}")
            y -= 14
            if y < 80:
                c.showPage()
                y = height - 40
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


# Recommendation engine — simple rules
def generate_recommendations(current_total: float, previous_total: Optional[float]) -> dict:
    recs = []
    message = ""
    if previous_total is None:
        # first report
        recs.append("No previous months to compare. Focus on reducing electricity and transport emissions.")
        message = "First recorded month. Track over time to see progress."
    else:
        diff = current_total - previous_total
        pct = (diff / previous_total * 100.0) if previous_total > 0 else 0
        if diff > 0:
            recs.append(f"Your emissions increased by {round(diff,2)} kgCO2e ({round(pct,2)}%). Consider:")
            recs.append(" - Reducing electricity use: switch to efficient appliances / shift to renewable tariff.")
            recs.append(" - Reducing car trips, carpool or use public transport.")
            if pct >= 10:
                recs.append(" - Consider reviewing diet (less red meat) and reduce food waste.")
            message = "High footprint compared to previous month."
        else:
            recs.append(f"Good job — emissions decreased by {round(-diff,2)} kgCO2e ({round(-pct,2)}%). Keep it up!")
            message = "Positive reduction from previous month."
    # Also give targeted recs if electricity or transport large proportion can be checked upstream by caller
    return {"recommendations": recs, "message": message}
