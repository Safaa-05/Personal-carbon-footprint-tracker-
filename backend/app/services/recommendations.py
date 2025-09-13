def get_recommendation(current, previous):
    if current > previous:
        return "Footprint increased. Consider reducing electricity use, travel, or waste."
    elif current < previous:
        return "Great job! Carbon footprint decreased compared to last month."
    else:
        return "No significant change. Try composting or switching to renewables for further improvement."
