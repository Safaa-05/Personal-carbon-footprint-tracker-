from fastapi import FastAPI
from utils.calculator import calculate_guest, calculate_logged

app = FastAPI()

@app.post("/calculate/guest")
def guest_calculate(data: dict):
    return calculate_guest(data)

@app.post("/calculate/logged")
def logged_calculate(data: dict):
    return calculate_logged(data)
