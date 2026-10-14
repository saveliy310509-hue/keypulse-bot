import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(title="KeyPulse Licensing System", version="1.0.0")

# Разрешаем CORS для взаимодействия с веб-клиентами и сторонними сайтами
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "licenses.db")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# --- Инициализация Базы Данных ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_code TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'available', -- available, activated, blocked, expired
                hwid TEXT,
                duration_days INTEGER DEFAULT 0, -- 0 = lifetime
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                activated_at TEXT,
                expires_at TEXT
            )
        """)
        conn.commit()

init_db()

# --- Вспомогательные функции ---
def format_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def make_key(prefix: str = "") -> str:
    clean_prefix = prefix.strip().upper()
    if clean_prefix and not clean_prefix.endswith("-"):
        clean_prefix += "-"
    token = uuid.uuid4().hex.upper()
    return f"{clean_prefix}{token[:4]}-{token[4:8]}-{token[8:12]}"

# --- Схемы Pydantic ---
class GenerateKeysRequest(BaseModel):
    count: int = 1
    prefix: str = "KEY"
    duration_days: int = 0
    note: str = ""

class ClientActivateRequest(BaseModel):
    key: str
    hwid: str
    admin_mode: bool = False

class ClientVerifyRequest(BaseModel):
    hwid: str
    admin_mode: bool = False

# --- Маршруты страниц ---
@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Панель управления не найдена</h1>", status_code=404)

# --- Маршруты Админ Панели ---
@app.get("/api/stats")
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM licenses GROUP BY status")
        counts = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM licenses")
        total = cursor.fetchone()[0]

    return {
        "total": total,
        "available": counts.get("available", 0),
        "activated": counts.get("activated", 0),
        "blocked": counts.get("blocked", 0),
        "expired": counts.get("expired", 0)
    }

@app.get("/api/keys")
def get_keys(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    query = "SELECT * FROM licenses WHERE 1=1"
    params = []

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if search:
        search_like = f"%{search.strip()}%"
        query += " AND (key_code LIKE ? OR hwid LIKE ? OR note LIKE ?)"
        params.extend([search_like, search_like, search_like])

    query += " ORDER BY id DESC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    keys = []
    now_str = format_now()
    for row in rows:
        d = dict(row)
        # Проверяем, не истек ли активированный ключ
        if d["status"] == "activated" and d["expires_at"]:
            if d["expires_at"] < now_str:
                d["status"] = "expired"
                with get_db() as update_conn:
                    update_conn.execute("UPDATE licenses SET status = 'expired' WHERE id = ?", (d["id"],))
        keys.append(d)

    return keys

@app.post("/api/keys/generate")
def generate_keys(req: GenerateKeysRequest):
    if req.count < 1 or req.count > 500:
        raise HTTPException(status_code=400, detail="Количество должно быть от 1 до 500")

    created_at = format_now()
    generated = []

    with get_db() as conn:
        cursor = conn.cursor()
        for _ in range(req.count):
            key_code = make_key(req.prefix)
            cursor.execute("""
                INSERT INTO licenses (key_code, status, duration_days, note, created_at)
                VALUES (?, 'available', ?, ?, ?)
            """, (key_code, req.duration_days, req.note, created_at))
            generated.append(key_code)
        conn.commit()

    return {"status": "success", "count": len(generated), "keys": generated}

@app.post("/api/keys/{key_code}/reset-hwid")
def reset_key_hwid(key_code: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE key_code = ?", (key_code,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ключ не найден")

        cursor.execute("""
            UPDATE licenses 
            SET hwid = NULL, status = 'available', activated_at = NULL, expires_at = NULL 
            WHERE key_code = ?
        """, (key_code,))
        conn.commit()

    return {"status": "success", "message": f"HWID для ключа {key_code} сброшен. Ключ снова свободен."}

@app.post("/api/keys/{key_code}/toggle-block")
def toggle_block_key(key_code: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM licenses WHERE key_code = ?", (key_code,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ключ не найден")

        current_status = row["status"]
        new_status = "blocked" if current_status != "blocked" else ("available" if not row.get("hwid") else "activated")

        cursor.execute("UPDATE licenses SET status = ? WHERE key_code = ?", (new_status, key_code))
        conn.commit()

    return {"status": "success", "new_status": new_status}

@app.delete("/api/keys/{key_code}")
def delete_key(key_code: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM licenses WHERE key_code = ?", (key_code,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ключ не найден")
        conn.commit()

    return {"status": "success", "message": "Ключ успешно удален"}

# --- Публичные Клиентские Эндпоинты (для приложения) ---
@app.post("/api/client/activate")
def client_activate(req: ClientActivateRequest):
    """
    Первичная активация ключа.
    Привязывает ключ к указанному HWID устройства.
    """
    key_clean = req.key.strip()
    hwid_clean = req.hwid.strip()

    if not key_clean or not hwid_clean:
        raise HTTPException(status_code=400, detail="Ключ и HWID не могут быть пустыми")

    now = datetime.utcnow()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE key_code = ?", (key_clean,))
        row = cursor.fetchone()

        if not row:
            if req.admin_mode:
                # В режиме админа создаем ключ на лету и активируем
                cursor.execute("""
                    INSERT INTO licenses (key_code, status, hwid, duration_days, note, created_at, activated_at)
                    VALUES (?, 'activated', ?, 0, 'Создан Администратором', ?, ?)
                """, (key_clean, hwid_clean, now_str, now_str))
                conn.commit()
                return {
                    "success": True,
                    "admin_override": True,
                    "message": "👑 [РЕЖИМ АДМИНА]: Новый ключ мгновенно сгенерирован и активирован без ограничений!",
                    "key": key_clean,
                    "activated_at": now_str,
                    "expires_at": None,
                    "is_lifetime": True
                }
            raise HTTPException(status_code=404, detail="Неверный ключ доступа.")

        status = row["status"]
        bound_hwid = row["hwid"]
        duration = row["duration_days"]

        # ЕСЛИ ВКЛЮЧЕН РЕЖИМ АДМИНИСТРАТОРА - обходим ЛЮБЫЕ ограничения:
        if req.admin_mode:
            return {
                "success": True,
                "admin_override": True,
                "message": f"👑 [РЕЖИМ АДМИНА]: Обход ограничений успешен! Ключ {key_clean} активирован бесконечно раз (Статус в базе: {status}).",
                "key": key_clean,
                "activated_at": now_str,
                "expires_at": None,
                "is_lifetime": True
            }

        if status == "blocked":
            raise HTTPException(status_code=403, detail="Этот ключ заблокирован администратором.")

        if status == "expired":
            raise HTTPException(status_code=403, detail="Срок действия этого ключа истек.")

        # Если ключ уже был активирован:
        if status == "activated":
            if bound_hwid == hwid_clean:
                # Это то же самое устройство - разрешаем вход
                return {
                    "success": True,
                    "message": "Ключ уже активирован на данном устройстве. Доступ предоставлен.",
                    "expires_at": row["expires_at"],
                    "is_lifetime": duration == 0
                }
            else:
                # Чужое устройство пытается ввести чужой ключ
                raise HTTPException(
                    status_code=409, 
                    detail="Ошибка! Этот ключ уже активирован на другом устройстве и не может быть использован повторно."
                )

        # Если ключ еще свободен (available)
        expires_at_str = None
        if duration > 0:
            expires_at = now + timedelta(days=duration)
            expires_at_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE licenses 
            SET status = 'activated', hwid = ?, activated_at = ?, expires_at = ?
            WHERE key_code = ?
        """, (hwid_clean, now_str, expires_at_str, key_clean))
        conn.commit()

    return {
        "success": True,
        "message": "Ключ успешно активирован и привязан к вашему устройству!",
        "key": key_clean,
        "activated_at": now_str,
        "expires_at": expires_at_str,
        "is_lifetime": duration == 0
    }

@app.post("/api/client/verify")
def client_verify(req: ClientVerifyRequest):
    """
    Проверка доступа при последующих запусках приложения.
    Передается только HWID устройства.
    """
    hwid_clean = req.hwid.strip()
    if not hwid_clean:
        raise HTTPException(status_code=400, detail="HWID обязателен")

    if req.admin_mode:
        return {
            "valid": True,
            "message": "👑 [РЕЖИМ АДМИНА]: Мастер-доступ подтвержден без ограничений.",
            "key": "ADMIN-MASTER-OVERRIDE",
            "expires_at": None,
            "is_lifetime": True
        }

    now_str = format_now()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE hwid = ? AND status = 'activated'", (hwid_clean,))
        row = cursor.fetchone()

        if not row:
            return {
                "valid": False, 
                "reason": "Для данного устройства нет активной лицензии. Требуется ввести ключ."
            }

        # Проверяем не истек ли срок
        expires_at = row["expires_at"]
        if expires_at and expires_at < now_str:
            cursor.execute("UPDATE licenses SET status = 'expired' WHERE id = ?", (row["id"],))
            conn.commit()
            return {
                "valid": False,
                "reason": "Срок действия лицензии истек."
            }

    return {
        "valid": True,
        "message": "Лицензия действительна.",
        "key": row["key_code"],
        "expires_at": expires_at,
        "is_lifetime": row["duration_days"] == 0
    }
