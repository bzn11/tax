import re

def normalize_roll_number(raw: str) -> str:
    return re.sub(r"[\s\-]", "", raw)

def is_valid_roll_number(roll: str) -> bool:
    return roll.isdigit() and 18 <= len(roll) <= 20
