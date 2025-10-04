from logging import config
from logging.config import fileConfig
# ...

# เดิม:
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# แก้เป็น (อย่างใดอย่างหนึ่ง)
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # ไม่มีส่วน logging ใน alembic.ini ก็ข้ามไป
        pass
