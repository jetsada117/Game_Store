
from datetime import datetime


def thai_date() -> str:
    now = datetime.now()
    thai_year = now.year + 543
    return f"{now.day:02}/{now.month:02}/{thai_year}"