from datetime import datetime
import secrets
import string

def thai_date() -> str:
    now = datetime.now()
    thai_year = now.year + 543
    return f"{now.day:02}/{now.month:02}/{thai_year}"


def _gen_code(length: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))