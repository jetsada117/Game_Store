import uuid
from app.core.supabase_client import supabase

BUCKET = "image_user" 

def upload_avatar(file_bytes: bytes, filename: str, content_type: str) -> str:
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
