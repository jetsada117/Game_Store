import uuid
from app.core.supabase_client import supabase

def upload_avatar(file_bytes: bytes, filename: str, content_type: str) -> str:
    BUCKET = "image_user" 

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    key = f"avatars/{uuid.uuid4()}.{ext}"

    sb = supabase
    sb.storage.from_(BUCKET).upload(
        key,
        file_bytes,
        file_options={"content-type": content_type}
    )
    url = sb.storage.from_(BUCKET).get_public_url(key)
    return url

def upload_game_image(file_bytes: bytes, filename: str, content_type: str) -> str:
    BUCKET = "image_user" 

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    key = f"games/{uuid.uuid4()}.{ext}"

    sb = supabase
    sb.storage.from_(BUCKET).upload(
        key,
        file_bytes,
        file_options={"content-type": content_type}
    )

    url = sb.storage.from_(BUCKET).get_public_url(key)
    return url