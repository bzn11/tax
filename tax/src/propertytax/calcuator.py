def calculate_estimated_tax(assessment_value, municipal_rate, education_rate):
    total_rate = municipal_rate + education_rate
    return round(assessment_value * total_rate, 2)
