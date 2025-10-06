# ⚡ FastAPI Backend Project

โปรเจกต์นี้เป็นโครงสร้างพื้นฐานของ **FastAPI** — เว็บเฟรมเวิร์กยุคใหม่สำหรับสร้าง RESTful API  
มีจุดเด่นด้านความเร็ว ความปลอดภัย และโครงสร้างที่เข้าใจง่าย  
รองรับการทำงานร่วมกับฐานข้อมูลผ่าน SQLAlchemy และรองรับการจัดการ environment แบบมืออาชีพ

---

## 🚀 เกี่ยวกับ FastAPI

**FastAPI** เป็นเฟรมเวิร์ก Python สำหรับสร้าง API ที่มีประสิทธิภาพสูง  
พัฒนาโดย Sebastián Ramírez ออกแบบให้ใช้งานง่ายและรองรับ **type hints** ของ Python เต็มรูปแบบ  

คุณสมบัติเด่นของ FastAPI:
- ⚡ **รวดเร็วมาก** — พัฒนาบน ASGI (ใช้ `Starlette`) เร็วกว่าหลายเฟรมเวิร์กแบบ synchronous
- 🔒 **ปลอดภัย** — รองรับ OAuth2, JWT, Password Hashing
- 🧠 **ตรวจสอบข้อมูลอัตโนมัติ** — ใช้ `Pydantic` ตรวจชนิดข้อมูลทั้ง request/response
- 🧩 **รองรับ Async/Await** — เขียนโค้ดแบบ asynchronous ได้เต็มรูปแบบ
- 🧰 **มีเอกสาร API อัตโนมัติ** — สร้างหน้า Swagger UI และ ReDoc ให้ทันที
- 🧑‍💻 **อ่านง่ายและเป็นมิตรกับนักพัฒนา** — ใช้ type hints และ autocompletion ได้เต็มที่ใน IDE

---

## 🧩 โครงสร้างพื้นฐานของโปรเจกต์

```bash
app/
│
├── main.py                # จุดเริ่มต้นของ FastAPI app
├── core/                  # การตั้งค่าและส่วนประกอบหลัก เช่น config, security
├── db/                    # การเชื่อมต่อฐานข้อมูล (SQLAlchemy)
├── schemas/               # Pydantic Models สำหรับ validate request/response
├── crud/                  # ฟังก์ชันจัดการฐานข้อมูล (Create, Read, Update, Delete)
├── controller/            # Router และ endpoint ของ API
└── services/              # ฟังก์ชันเสริม เช่น upload, auth, etc.
