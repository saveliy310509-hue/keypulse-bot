import asyncio
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from aiogram.exceptions import TelegramBadRequest

# =========================================================================
# 1. ЗАГРУЗКА КОНФИГУРАЦИИ ИЗ .ENV
# =========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("TOKENBOT", "")
ADMIN_ID = int(os.getenv("ADMINID", "0"))
PROXY = os.getenv("PROXY", None)

if not TOKEN:
    print("[!] ПРЕДУПРЕЖДЕНИЕ: Переменная TOKENBOT не найдена в .env или окружении!", flush=True)

DB_PATH = os.path.join(BASE_DIR, "licenses.db")

# =========================================================================
# 2. ПРЕМИУМ ЭМОДЗИ (Telegram iOS Icons с https://emoji.wivvi.net/)
# =========================================================================
# ID эмодзи для кнопок (icon_custom_emoji_id) и тегов <tg-emoji>
ID_CROWN = "5805553606635559688"      # 👑 Корона
ID_LIGHTNING = "5884428842780594914"  # ⚡ Молния
ID_CHECK = "5774022692642492953"      # ✅ Галочка
ID_LOCK = "6037249452824072506"       # 🔒 Замок закрытый
ID_UNLOCK = "6037496202990194718"     # 🔓 Замок открытый
ID_TRASH = "6039522349517115015"      # 🗑 Мусорный бак
ID_GEAR = "6032742198179532882"       # ⚙ Настройки
ID_ROBOT = "6030400221232501136"      # 🤖 Бот
ID_CHART = "5938539885907415367"      # 📈 Рост график
ID_LIST = "5766994197705921104"       # 🗂 Список
ID_SEARCH = "6032850693348399258"     # 🔎 Поиск
ID_BACK = "5960671702059848143"       # ⬅️ Назад
ID_REPEAT = "6030657343744644592"     # 🔁 Повтор
ID_TAG = "5886285355279193209"        # 🏷 Тег
ID_DOWNLOAD = "6039802767931871481"   # ⬇️ Скачать
ID_DIAMOND = "6037083366438737901"    # 💎 Алмаз
ID_CLOCK = "5983150113483134607"      # ⏰️ Часы
ID_NEW = "5895669571058142797"        # 🆕 NEW
ID_STAR = "6028338546736107668"       # ⭐️ Звезда
ID_SPARKLES = "5940660740758184142"   # ✨ AI / Свечение
ID_CROSS = "6030757850274336631"      # ❌ Крестик
ID_USER = "6035084557378654059"       # 👤 Профиль
ID_SHIELD = "6030445631921721471"     # 🛡 Щит галочка
ID_EDIT = "6039779802741739617"       # ✏️ Редактировать
ID_DESKTOP = "5942734685976138521"    # 🖥 ПК Finder
ID_COPY = "6034969813032374911"       # 📄 Копировать
ID_INFO = "6028435952299413210"       # ℹ Инфо
ID_FILE = "6037475557082403885"       # 📁 Файл
ID_SLIDERS = "5771449289972650710"    # 🎛 Ползунки

# Теги HTML для текста сообщений (<tg-emoji>)
PE_CROWN = f'<tg-emoji emoji-id="{ID_CROWN}">👑</tg-emoji>'
PE_LIGHTNING = f'<tg-emoji emoji-id="{ID_LIGHTNING}">⚡</tg-emoji>'
PE_CHECK = f'<tg-emoji emoji-id="{ID_CHECK}">✅</tg-emoji>'
PE_LOCK = f'<tg-emoji emoji-id="{ID_LOCK}">🔒</tg-emoji>'
PE_UNLOCK = f'<tg-emoji emoji-id="{ID_UNLOCK}">🔓</tg-emoji>'
PE_TRASH = f'<tg-emoji emoji-id="{ID_TRASH}">🗑</tg-emoji>'
PE_GEAR = f'<tg-emoji emoji-id="{ID_GEAR}">⚙</tg-emoji>'
PE_ROBOT = f'<tg-emoji emoji-id="{ID_ROBOT}">🤖</tg-emoji>'
PE_CHART = f'<tg-emoji emoji-id="{ID_CHART}">📈</tg-emoji>'
PE_LIST = f'<tg-emoji emoji-id="{ID_LIST}">🗂</tg-emoji>'
PE_SEARCH = f'<tg-emoji emoji-id="{ID_SEARCH}">🔎</tg-emoji>'
PE_BACK = f'<tg-emoji emoji-id="{ID_BACK}">⬅️</tg-emoji>'
PE_REPEAT = f'<tg-emoji emoji-id="{ID_REPEAT}">🔁</tg-emoji>'
PE_TAG = f'<tg-emoji emoji-id="{ID_TAG}">🏷</tg-emoji>'
PE_DOWNLOAD = f'<tg-emoji emoji-id="{ID_DOWNLOAD}">⬇️</tg-emoji>'
PE_DIAMOND = f'<tg-emoji emoji-id="{ID_DIAMOND}">💎</tg-emoji>'
PE_CLOCK = f'<tg-emoji emoji-id="{ID_CLOCK}">⏰️</tg-emoji>'
PE_NEW = f'<tg-emoji emoji-id="{ID_NEW}">🆕</tg-emoji>'
PE_STAR = f'<tg-emoji emoji-id="{ID_STAR}">⭐️</tg-emoji>'
PE_SPARKLES = f'<tg-emoji emoji-id="{ID_SPARKLES}">✨</tg-emoji>'
PE_CROSS = f'<tg-emoji emoji-id="{ID_CROSS}">❌</tg-emoji>'
PE_USER = f'<tg-emoji emoji-id="{ID_USER}">👤</tg-emoji>'
PE_SHIELD = f'<tg-emoji emoji-id="{ID_SHIELD}">🛡</tg-emoji>'
PE_EDIT = f'<tg-emoji emoji-id="{ID_EDIT}">✏️</tg-emoji>'
PE_DESKTOP = f'<tg-emoji emoji-id="{ID_DESKTOP}">🖥</tg-emoji>'
PE_COPY = f'<tg-emoji emoji-id="{ID_COPY}">📄</tg-emoji>'
PE_INFO = f'<tg-emoji emoji-id="{ID_INFO}">ℹ</tg-emoji>'
PE_FILE = f'<tg-emoji emoji-id="{ID_FILE}">📁</tg-emoji>'
PE_SLIDERS = f'<tg-emoji emoji-id="{ID_SLIDERS}">🎛</tg-emoji>'

# =========================================================================
# 3. БАЗА ДАННЫХ (SQLite)
# =========================================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

EMOJI_GALLERY = [
    ("👑", "Корона", ID_CROWN),
    ("⚡", "Молния", ID_LIGHTNING),
    ("✅", "Галочка", ID_CHECK),
    ("🔒", "Замок", ID_LOCK),
    ("🔓", "Открыт", ID_UNLOCK),
    ("⚙️", "Настройки", ID_GEAR),
    ("🤖", "Робот", ID_ROBOT),
    ("📈", "График", ID_CHART),
    ("🗂", "Список", ID_LIST),
    ("🔎", "Поиск", ID_SEARCH),
    ("⭐️", "Звезда", ID_STAR),
    ("✨", "Свечение", ID_SPARKLES),
    ("💎", "Алмаз", ID_DIAMOND),
    ("👤", "Профиль", ID_USER),
    ("🛡", "Щит", ID_SHIELD),
    ("✏️", "Карандаш", ID_EDIT),
    ("📁", "Папка", ID_FILE),
    ("⏰", "Часы", ID_CLOCK),
    ("🆕", "NEW", ID_NEW),
    ("📄", "Документ", ID_COPY),
    ("🖥", "ПК", ID_DESKTOP),
    ("🔁", "Повтор", ID_REPEAT),
    ("🏷", "Тег", ID_TAG),
    ("⬇️", "Скачать", ID_DOWNLOAD),
    ("🗑", "Корзина", ID_TRASH),
    ("❌", "Крестик", ID_CROSS),
    ("⬅️", "Назад", ID_BACK),
]

DEFAULT_SCREENS = {
    "user_main": {
        "title": "👤 Главное меню пользователя",
        "is_system": 1,
        "text": (
            f"{PE_SHIELD} <b>KEYPULSE.AI // ЛИЦЕНЗИРОВАНИЕ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Здравствуйте, <b>{{user_name}}</b>!\n"
            f"Добро пожаловать в персональный центр лицензирования KeyPulse.\n\n"
            f"{PE_LOCK} Здесь вы можете активировать лицензионный ключ для вашего приложения или проверить срок действия текущей подписки.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Выберите пункт в меню ниже:</i>"
        ),
        "buttons": [
            {"text": "Активировать ключ", "emoji": ID_LOCK, "type": "callback", "value": "user_activate_prompt", "row": 0, "col": 0},
            {"text": "Моя лицензия", "emoji": ID_USER, "type": "callback", "value": "user_my_status", "row": 1, "col": 0},
            {"text": "О системе", "emoji": ID_INFO, "type": "callback", "value": "about_info", "row": 2, "col": 0},
        ]
    },
    "about_info": {
        "title": "ℹ️ О системе",
        "is_system": 1,
        "text": (
            f"{PE_INFO} <b>О СИСТЕМЕ ЛИЦЕНЗИРОВАНИЯ KEYPULSE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>KeyPulse</b> — защищенный сервис одноразовых лицензий с привязкой к железу (HWID).\n\n"
            f"• <b>Защита от повторного ввода:</b> Каждый ключ уникален и при первой активации связывается с устройством пользователя.\n"
            f"• <b>Синхронизация:</b> Бот работает в единой базе с веб-панелью и клиентами приложения.\n"
            f"• <b>Поддержка:</b> По всем вопросам обращайтесь к администратору.\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        "buttons": [
            {"text": "Назад", "emoji": ID_BACK, "type": "callback", "value": "to_main_menu", "row": 0, "col": 0},
        ]
    },
    "admin_main": {
        "title": "👑 Главное меню администратора",
        "is_system": 1,
        "text": (
            f"{PE_SHIELD} <b>KEYPULSE.AI // СИСТЕМА ЛИЦЕНЗИРОВАНИЯ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE_USER} <b>Администратор:</b> <code>{{user_name}}</code>\n"
            f"{PE_ROBOT} <b>База Данных:</b> <code>ONLINE // SQLITE</code>\n\n"
            f"{PE_CHART} <b>СТАТИСТИКА ЛИЦЕНЗИЙ:</b>\n"
            f"  {PE_LIST} Всего в базе: <b>{{stats_total}}</b> шт.\n"
            f"  {PE_CHECK} Свободны для ввода: <b>{{stats_available}}</b> шт.\n"
            f"  {PE_LIGHTNING} Активированы (HWID): <b>{{stats_activated}}</b> шт.\n"
            f"  {PE_CROSS} Заблокированы/Истекли: <b>{{stats_blocked_expired}}</b> шт.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Выберите действие в меню управления:</i>"
        ),
        "buttons": [
            {"text": "Создать ключи", "emoji": ID_NEW, "type": "callback", "value": "gen_menu", "row": 0, "col": 0},
            {"text": "Список ключей", "emoji": ID_LIST, "type": "callback", "value": "keys_list:all:0", "row": 0, "col": 1},
            {"text": "Тестер клиента", "emoji": ID_LIGHTNING, "type": "callback", "value": "tester_menu", "row": 1, "col": 0},
            {"text": "Поиск по базе", "emoji": ID_SEARCH, "type": "callback", "value": "search_prompt", "row": 1, "col": 1},
            {"text": "Конструктор бота", "emoji": ID_GEAR, "type": "callback", "value": "cns_main", "row": 2, "col": 0},
            {"text": "Экспорт в TXT", "emoji": ID_DOWNLOAD, "type": "callback", "value": "export_menu", "row": 3, "col": 0},
            {"text": "Обновить", "emoji": ID_REPEAT, "type": "callback", "value": "refresh_main", "row": 3, "col": 1},
        ]
    },
    "user_activate_prompt": {
        "title": "🔒 Ввод ключа (Активация)",
        "is_system": 1,
        "text": (
            f"{PE_LOCK} <b>АКТИВАЦИЯ ЛИЦЕНЗИОННОГО КЛЮЧА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Отправьте в чат ваш лицензионный ключ (например, <code>PRO-A1B2-C3D4-E5F6</code>):\n\n"
            f"<i>(Ваше сообщение будет автоматически удалено после проверки)</i>"
        ),
        "buttons": [
            {"text": "Отмена", "emoji": ID_CROSS, "type": "callback", "value": "to_main_menu", "row": 0, "col": 0},
        ]
    },
    "user_my_status": {
        "title": "👤 Экран «Моя лицензия» (без подписки)",
        "is_system": 1,
        "text": (
            f"{PE_LOCK} <b>У ВАС НЕТ АКТИВНОЙ ЛИЦЕНЗИИ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Для вашего Telegram аккаунта не найдено активных подписок.\n\n"
            f"<i>Если у вас есть лицензионный ключ, нажмите кнопку «Активировать ключ» ниже:</i>"
        ),
        "buttons": [
            {"text": "Активировать ключ", "emoji": ID_LOCK, "type": "callback", "value": "user_activate_prompt", "row": 0, "col": 0},
            {"text": "Главное меню", "emoji": ID_BACK, "type": "callback", "value": "to_main_menu", "row": 1, "col": 0},
        ]
    },
    "export_menu": {
        "title": "⬇️ Меню экспорта ключей",
        "is_system": 1,
        "text": (
            f"{PE_DOWNLOAD} <b>ЭКСПОРТ ЛИЦЕНЗИЙ // BACKUP</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Выгрузка свободных ключей в формате текстового документа (.txt)\n"
            f"для удобного распространения или резервного хранения.\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        "buttons": [
            {"text": "Скачать свободные (TXT)", "emoji": ID_DOWNLOAD, "type": "callback", "value": "export_run", "row": 0, "col": 0},
            {"text": "Главное меню", "emoji": ID_BACK, "type": "callback", "value": "to_main_menu", "row": 1, "col": 0},
        ]
    },
    "tester_menu": {
        "title": "⚡ Симулятор клиентского ПК",
        "is_system": 1,
        "text": (
            f"{PE_DESKTOP} <b>СИМУЛЯТОР КЛИЕНТСКОГО ПК // TESTER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE_LIGHTNING} <b>Виртуальный HWID ПК:</b> <code>{{test_hwid}}</code>\n"
            f"{PE_DIAMOND} <b>Тестовый ключ:</b> {{key_display}}\n\n"
            f"<b>TERMINAL // CLIENT_LOG:</b>\n"
            f"<code>{{terminal_log}}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Выберите действие для тестирования:</i>"
        ),
        "buttons": [
            {"text": "1. Активировать", "emoji": ID_LIGHTNING, "type": "callback", "value": "tester_exec_activate", "row": 0, "col": 0},
            {"text": "2. Проверить (Verify)", "emoji": ID_CHECK, "type": "callback", "value": "tester_exec_verify", "row": 0, "col": 1},
            {"text": "Сменить ПК (Новый HWID)", "emoji": ID_REPEAT, "type": "callback", "value": "tester_randomize_hwid", "row": 1, "col": 0},
            {"text": "Взять ключ из базы", "emoji": ID_TAG, "type": "callback", "value": "tester_pick_free_key", "row": 2, "col": 0},
            {"text": "Ввести ключ вручную", "emoji": ID_EDIT, "type": "callback", "value": "tester_prompt_key", "row": 2, "col": 1},
            {"text": "Ввести свой HWID", "emoji": ID_DESKTOP, "type": "callback", "value": "tester_prompt_hwid", "row": 3, "col": 0},
            {"text": "Главное меню", "emoji": ID_BACK, "type": "callback", "value": "to_main_menu", "row": 3, "col": 1},
        ]
    }
}

def reset_screen_to_default(screen_key: str):
    if screen_key not in DEFAULT_SCREENS:
        return False
    data = DEFAULT_SCREENS[screen_key]
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("""
            INSERT INTO bot_screens (screen_key, title, message_text, is_system, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(screen_key) DO UPDATE SET
                title = excluded.title,
                message_text = excluded.message_text,
                updated_at = excluded.updated_at
        """, (screen_key, data["title"], data["text"], data.get("is_system", 1), now_str))
        
        conn.execute("DELETE FROM bot_buttons WHERE screen_key = ?", (screen_key,))
        
        for idx, btn in enumerate(data.get("buttons", [])):
            conn.execute("""
                INSERT INTO bot_buttons (screen_key, btn_text, icon_emoji_id, action_type, action_value, row_index, col_index, is_active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (screen_key, btn["text"], btn.get("emoji", ""), btn.get("type", "callback"), btn.get("value", ""), btn.get("row", 0), btn.get("col", 0), idx))
        conn.commit()
    return True

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_code TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                hwid TEXT,
                duration_days INTEGER DEFAULT 0,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                activated_at TEXT,
                expires_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_screens (
                screen_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message_text TEXT NOT NULL,
                is_system INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screen_key TEXT NOT NULL,
                btn_text TEXT NOT NULL,
                icon_emoji_id TEXT DEFAULT '',
                action_type TEXT NOT NULL DEFAULT 'callback',
                action_value TEXT NOT NULL,
                row_index INTEGER DEFAULT 0,
                col_index INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM bot_screens")
        if c.fetchone()[0] == 0:
            for s_key in DEFAULT_SCREENS:
                reset_screen_to_default(s_key)

init_db()

def get_screen_text(screen_key: str, default_val: str = "") -> str:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT message_text FROM bot_screens WHERE screen_key = ?", (screen_key,))
        row = c.fetchone()
        if row and row["message_text"]:
            return row["message_text"]
    if screen_key in DEFAULT_SCREENS:
        return DEFAULT_SCREENS[screen_key]["text"]
    return default_val

def get_screen_keyboard(screen_key: str) -> InlineKeyboardMarkup:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, btn_text, icon_emoji_id, action_type, action_value, row_index, col_index 
            FROM bot_buttons 
            WHERE screen_key = ? AND is_active = 1 
            ORDER BY row_index ASC, sort_order ASC, id ASC
        """, (screen_key,))
        rows = c.fetchall()

    if not rows:
        return InlineKeyboardMarkup(inline_keyboard=[])

    grid = {}
    for r in rows:
        r_idx = r["row_index"]
        if r_idx not in grid:
            grid[r_idx] = []
        kw = {"text": r["btn_text"]}
        if r["icon_emoji_id"] and str(r["icon_emoji_id"]).strip():
            kw["icon_custom_emoji_id"] = str(r["icon_emoji_id"]).strip()
        if r["action_type"] == "url":
            kw["url"] = r["action_value"]
        else:
            kw["callback_data"] = r["action_value"]
        grid[r_idx].append(InlineKeyboardButton(**kw))

    keyboard = [grid[k] for k in sorted(grid.keys())]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def format_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def make_key(prefix: str = "PRO") -> str:
    clean_prefix = prefix.strip().upper()
    if clean_prefix and not clean_prefix.endswith("-"):
        clean_prefix += "-"
    token = uuid.uuid4().hex.upper()
    return f"{clean_prefix}{token[:4]}-{token[4:8]}-{token[8:12]}"

def check_expired_licenses():
    """Синхронизация просроченных лицензий как в FastAPI app.py"""
    now_str = format_now()
    with get_db() as conn:
        conn.execute("""
            UPDATE licenses 
            SET status = 'expired' 
            WHERE status = 'activated' AND expires_at IS NOT NULL AND expires_at < ?
        """, (now_str,))
        conn.commit()

# =========================================================================
# 4. FSM СОСТОЯНИЯ (Для ввода информации без лишних сообщений в чате)
# =========================================================================
class PanelStates(StatesGroup):
    waiting_key_activate = State()    # Активация ключа пользователем
    waiting_search_query = State()    # Поиск по базе
    waiting_custom_prefix = State()   # Ввод своего префикса в генераторе
    waiting_custom_count = State()    # Ввод своего количества в генераторе
    waiting_custom_duration = State() # Ввод своего срока в генераторе
    waiting_custom_note = State()     # Ввод своей заметки в генераторе
    waiting_edit_note = State()       # Редактирование заметки ключа
    waiting_test_key = State()        # Ввод ключа в симуляторе
    waiting_test_hwid = State()       # Ввод своего HWID в симуляторе

    # Состояния Конструктора Бота
    cns_edit_text = State()           # Ввод нового текста экрана
    cns_new_screen_key = State()      # Ввод ключа нового экрана
    cns_new_screen_title = State()    # Ввод заголовка нового экрана
    cns_new_screen_text = State()     # Ввод текста нового экрана
    cns_btn_new_text = State()        # Ввод текста новой кнопки
    cns_btn_new_action = State()      # Ввод действия новой кнопки
    cns_btn_edit_text = State()       # Редактирование текста кнопки
    cns_btn_edit_action = State()     # Редактирование действия кнопки
    cns_btn_custom_emoji = State()    # Ввод кастомного ID эмодзи

# =========================================================================
# 5. СИСТЕМА ОДНОГО СООБЩЕНИЯ (Single-Message Controller)
# =========================================================================
from aiogram.client.session.aiohttp import AiohttpSession

def make_bot_session(proxy_url: Optional[str]) -> AiohttpSession:
    if not proxy_url:
        return AiohttpSession()
    if proxy_url.startswith("socks5://") or proxy_url.startswith("socks4://"):
        from aiohttp_socks import ProxyConnector
        class SocksSession(AiohttpSession):
            async def create_session(self):
                if self._session is None or self._session.closed:
                    import aiohttp
                    conn = ProxyConnector.from_url(proxy_url)
                    self._session = aiohttp.ClientSession(
                        connector=conn,
                        headers={"User-Agent": "aiogram 3.31 Telegram Bot"}
                    )
                return self._session
        return SocksSession()
    return AiohttpSession(proxy=proxy_url)

session = make_bot_session(PROXY)
bot = Bot(token=TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Хранилище ID главного сообщения для каждого чата
user_panels: Dict[int, int] = {}

async def render_panel(chat_id: int, text: str, keyboard: InlineKeyboardMarkup, user_id: int = None):
    """
    Редактирует существующее сообщение панели.
    Если сообщение не найдено или удалено, отправляет новое и запоминает его.
    Всегда оставляет ровно 1 интерактивное сообщение!
    """
    msg_id = user_panels.get(chat_id)
    if msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return
            # Если сообщение удалено или недоступно - отправляем заново
            pass
        except Exception:
            pass

    # Отправляем новое сообщение
    sent = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    user_panels[chat_id] = sent.message_id

# =========================================================================
# 6. ГЛАВНОЕ МЕНЮ (DASHBOARD)
# =========================================================================
def get_stats_data():
    check_expired_licenses()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT status, COUNT(*) FROM licenses GROUP BY status")
        counts = dict(c.fetchall())
        c.execute("SELECT COUNT(*) FROM licenses")
        total = c.fetchone()[0]
    return {
        "total": total,
        "available": counts.get("available", 0),
        "activated": counts.get("activated", 0),
        "blocked": counts.get("blocked", 0),
        "expired": counts.get("expired", 0)
    }

def main_menu_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    screen_key = "admin_main" if is_admin else "user_main"
    return get_screen_keyboard(screen_key)

def main_menu_text(is_admin: bool, user_name: str) -> str:
    stats = get_stats_data()
    blocked_or_expired = stats["blocked"] + stats["expired"]

    if is_admin:
        default_tpl = (
            f"{PE_SHIELD} <b>KEYPULSE.AI // СИСТЕМА ЛИЦЕНЗИРОВАНИЯ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE_USER} <b>Администратор:</b> <code>{{user_name}}</code>\n"
            f"{PE_ROBOT} <b>База Данных:</b> <code>ONLINE // SQLITE</code>\n\n"
            f"{PE_CHART} <b>СТАТИСТИКА ЛИЦЕНЗИЙ:</b>\n"
            f"  {PE_LIST} Всего в базе: <b>{{stats_total}}</b> шт.\n"
            f"  {PE_CHECK} Свободны для ввода: <b>{{stats_available}}</b> шт.\n"
            f"  {PE_LIGHTNING} Активированы (HWID): <b>{{stats_activated}}</b> шт.\n"
            f"  {PE_CROSS} Заблокированы/Истекли: <b>{{stats_blocked_expired}}</b> шт.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Выберите действие в меню управления:</i>"
        )
        tpl = get_screen_text("admin_main", default_tpl)
        try:
            return tpl.format(
                user_name=user_name,
                stats_total=stats["total"],
                stats_available=stats["available"],
                stats_activated=stats["activated"],
                stats_blocked_expired=blocked_or_expired
            )
        except Exception:
            return tpl
    else:
        default_tpl = (
            f"{PE_SHIELD} <b>KEYPULSE.AI // ЛИЦЕНЗИРОВАНИЕ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Здравствуйте, <b>{{user_name}}</b>!\n"
            f"Добро пожаловать в персональный центр лицензирования KeyPulse.\n\n"
            f"{PE_LOCK} Здесь вы можете активировать лицензионный ключ для вашего приложения или проверить срок действия текущей подписки.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Выберите пункт в меню ниже:</i>"
        )
        tpl = get_screen_text("user_main", default_tpl)
        try:
            return tpl.format(user_name=user_name)
        except Exception:
            return tpl

# =========================================================================
# 7. ХЕНДЛЕР /START
# =========================================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    # Удаляем сообщение пользователя с /start для чистоты чата
    try:
        await message.delete()
    except Exception:
        pass

    is_admin = (message.from_user.id == ADMIN_ID)
    text = main_menu_text(is_admin, message.from_user.full_name)
    kb = main_menu_keyboard(is_admin)
    await render_panel(message.chat.id, text, kb, message.from_user.id)

@dp.callback_query(F.data == "refresh_main")
async def cb_refresh_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = (callback.from_user.id == ADMIN_ID)
    text = main_menu_text(is_admin, callback.from_user.full_name)
    kb = main_menu_keyboard(is_admin)
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer("Данные обновлены!")

@dp.callback_query(F.data == "to_main_menu")
async def cb_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = (callback.from_user.id == ADMIN_ID)
    text = main_menu_text(is_admin, callback.from_user.full_name)
    kb = main_menu_keyboard(is_admin)
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

# =========================================================================
# 9. КИБЕР-ГЕНЕРАТОР КЛЮЧЕЙ (КАК В МОДАЛКЕ НА САЙТЕ)
# =========================================================================
def generator_keyboard(count: int, prefix: str, duration: int, note: str) -> InlineKeyboardMarkup:
    dur_str = "Lifetime (0 дн.)" if duration == 0 else f"{duration} дн."
    note_str = note if note else "Без заметки"
    if len(note_str) > 16:
        note_str = note_str[:14] + ".."

    buttons = [
        [
            InlineKeyboardButton(text=f"Кол-во: {count} шт.", callback_data="gen_count_cycle", icon_custom_emoji_id=ID_TAG),
            InlineKeyboardButton(text="Своё число", callback_data="gen_prompt_count", icon_custom_emoji_id=ID_EDIT),
        ],
        [
            InlineKeyboardButton(text=f"Префикс: {prefix}", callback_data="gen_prefix_cycle", icon_custom_emoji_id=ID_DIAMOND),
            InlineKeyboardButton(text="Свой префикс", callback_data="gen_prompt_prefix", icon_custom_emoji_id=ID_EDIT),
        ],
        [
            InlineKeyboardButton(text=f"Срок: {dur_str}", callback_data="gen_dur_cycle", icon_custom_emoji_id=ID_CLOCK),
            InlineKeyboardButton(text="Свой срок", callback_data="gen_prompt_duration", icon_custom_emoji_id=ID_EDIT),
        ],
        [
            InlineKeyboardButton(text=f"Заметка: {note_str}", callback_data="gen_note_cycle", icon_custom_emoji_id=ID_FILE),
            InlineKeyboardButton(text="Своя заметка", callback_data="gen_prompt_note", icon_custom_emoji_id=ID_EDIT),
        ],
        [
            InlineKeyboardButton(text="Случайный образец", callback_data="gen_shuffle_preview", icon_custom_emoji_id=ID_REPEAT),
        ],
        [
            InlineKeyboardButton(text="Сгенерировать партию", callback_data="gen_execute", icon_custom_emoji_id=ID_SPARKLES),
        ],
        [
            InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "gen_menu")
async def cb_gen_menu(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступно только админу", show_alert=True)
        return

    data = await state.get_data()
    count = data.get("gen_count", 5)
    prefix = data.get("gen_prefix", "PRO")
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "@Telegram")
    sample_key = data.get("sample_key", make_key(prefix))

    await state.update_data(
        gen_count=count,
        gen_prefix=prefix,
        gen_duration=duration,
        gen_note=note,
        sample_key=sample_key
    )

    dur_display = "Бессрочная (Lifetime)" if duration == 0 else f"{duration} дней"

    text = (
        f"{PE_SPARKLES} <b>ГЕНЕРАТОР ЛИЦЕНЗИЙ // KEY GEN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_CHECK} <b>ЖИВОЙ ОБРАЗЕЦ КЛЮЧА:</b>\n"
        f"<code>{sample_key}</code>\n\n"
        f"<b>Параметры создаваемой партии:</b>\n"
        f"  {PE_TAG} Количество: <b>{count} шт.</b>\n"
        f"  {PE_DIAMOND} Префикс серии: <code>{prefix}-...</code>\n"
        f"  {PE_CLOCK} Срок действия: <b>{dur_display}</b>\n"
        f"  {PE_FILE} Примечание: <i>{note or '—'}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Нажмите на параметр для быстрой смены или подтвердите создание:</i>"
    )
    kb = generator_keyboard(count, prefix, duration, note)
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data == "gen_count_cycle")
async def cb_gen_count_cycle(callback: CallbackQuery, state: FSMContext):
    counts = [1, 5, 10, 25, 50, 100]
    data = await state.get_data()
    cur = data.get("gen_count", 5)
    idx = (counts.index(cur) + 1) % len(counts) if cur in counts else 0
    await state.update_data(gen_count=counts[idx])
    await cb_gen_menu(callback, state)

@dp.callback_query(F.data == "gen_prefix_cycle")
async def cb_gen_prefix_cycle(callback: CallbackQuery, state: FSMContext):
    prefixes = ["PRO", "VIP", "GAME", "ELITE", "ALPHA", "TEST", "KEY"]
    data = await state.get_data()
    cur = data.get("gen_prefix", "PRO")
    idx = (prefixes.index(cur) + 1) % len(prefixes) if cur in prefixes else 0
    new_prefix = prefixes[idx]
    await state.update_data(gen_prefix=new_prefix, sample_key=make_key(new_prefix))
    await cb_gen_menu(callback, state)

@dp.callback_query(F.data == "gen_dur_cycle")
async def cb_gen_dur_cycle(callback: CallbackQuery, state: FSMContext):
    durations = [0, 7, 30, 90, 365]
    data = await state.get_data()
    cur = data.get("gen_duration", 30)
    idx = (durations.index(cur) + 1) % len(durations) if cur in durations else 0
    await state.update_data(gen_duration=durations[idx])
    await cb_gen_menu(callback, state)

@dp.callback_query(F.data == "gen_note_cycle")
async def cb_gen_note_cycle(callback: CallbackQuery, state: FSMContext):
    notes = ["@Telegram", "Discord VIP", "Тестер", "Продажа", "Клиент", ""]
    data = await state.get_data()
    cur = data.get("gen_note", "@Telegram")
    idx = (notes.index(cur) + 1) % len(notes) if cur in notes else 0
    await state.update_data(gen_note=notes[idx])
    await cb_gen_menu(callback, state)

@dp.callback_query(F.data == "gen_shuffle_preview")
async def cb_gen_shuffle(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prefix = data.get("gen_prefix", "PRO")
    await state.update_data(sample_key=make_key(prefix))
    await cb_gen_menu(callback, state)

# Ручной ввод параметров партии через чат
@dp.callback_query(F.data == "gen_prompt_count")
async def cb_gen_prompt_count(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_custom_count)
    text = (
        f"{PE_TAG} <b>ВВОД КОЛИЧЕСТВА КЛЮЧЕЙ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте в чат число от <b>1</b> до <b>500</b>:\n"
        f"<i>(Ваше сообщение будет мгновенно удалено, а панель обновится)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="gen_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_custom_count)
async def process_custom_count(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    try:
        val = int(message.text.strip())
        if 1 <= val <= 500:
            await state.update_data(gen_count=val)
    except Exception:
        pass

    await state.set_state(None)
    data = await state.get_data()
    prefix = data.get("gen_prefix", "PRO")
    count = data.get("gen_count", 5)
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "@Telegram")
    sample_key = data.get("sample_key", make_key(prefix))

    dur_display = "Бессрочная (Lifetime)" if duration == 0 else f"{duration} дней"
    text = (
        f"{PE_SPARKLES} <b>ГЕНЕРАТОР ЛИЦЕНЗИЙ // KEY GEN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_CHECK} <b>ЖИВОЙ ОБРАЗЕЦ КЛЮЧА:</b>\n"
        f"<code>{sample_key}</code>\n\n"
        f"<b>Параметры создаваемой партии:</b>\n"
        f"  {PE_TAG} Количество: <b>{count} шт.</b>\n"
        f"  {PE_DIAMOND} Префикс серии: <code>{prefix}-...</code>\n"
        f"  {PE_CLOCK} Срок действия: <b>{dur_display}</b>\n"
        f"  {PE_FILE} Примечание: <i>{note or '—'}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Нажмите на параметр для изменения или подтвердите создание:</i>"
    )
    kb = generator_keyboard(count, prefix, duration, note)
    await render_panel(message.chat.id, text, kb)

@dp.callback_query(F.data == "gen_prompt_prefix")
async def cb_gen_prompt_prefix(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_custom_prefix)
    text = (
        f"{PE_DIAMOND} <b>ВВОД ПРЕФИКСА СЕРИИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте в ответ желаемый префикс (например: <code>VIP</code>, <code>GAME</code>, <code>PREMIUM</code>):\n"
        f"<i>(Ваше сообщение будет мгновенно удалено, а панель обновится)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="gen_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_custom_prefix)
async def process_custom_prefix(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    pref = message.text.strip().upper()[:8]
    if pref:
        await state.update_data(gen_prefix=pref, sample_key=make_key(pref))

    await state.set_state(None)
    data = await state.get_data()
    prefix = data.get("gen_prefix", "PRO")
    count = data.get("gen_count", 5)
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "@Telegram")
    sample_key = data.get("sample_key", make_key(prefix))

    dur_display = "Бессрочная (Lifetime)" if duration == 0 else f"{duration} дней"
    text = (
        f"{PE_SPARKLES} <b>ГЕНЕРАТОР ЛИЦЕНЗИЙ // KEY GEN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_CHECK} <b>ЖИВОЙ ОБРАЗЕЦ КЛЮЧА:</b>\n"
        f"<code>{sample_key}</code>\n\n"
        f"<b>Параметры создаваемой партии:</b>\n"
        f"  {PE_TAG} Количество: <b>{count} шт.</b>\n"
        f"  {PE_DIAMOND} Префикс серии: <code>{prefix}-...</code>\n"
        f"  {PE_CLOCK} Срок действия: <b>{dur_display}</b>\n"
        f"  {PE_FILE} Примечание: <i>{note or '—'}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Нажмите на параметр для изменения или подтвердите создание:</i>"
    )
    kb = generator_keyboard(count, prefix, duration, note)
    await render_panel(message.chat.id, text, kb)

@dp.callback_query(F.data == "gen_prompt_duration")
async def cb_gen_prompt_duration(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_custom_duration)
    text = (
        f"{PE_CLOCK} <b>ВВОД СРОКА ДЕЙСТВИЯ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте срок действия в днях (число):\n"
        f"• <code>0</code> — Бессрочная лицензия (Lifetime)\n"
        f"• <code>1</code>, <code>7</code>, <code>30</code>, <code>90</code>, <code>365</code> — дни\n"
        f"<i>(Ваше сообщение будет мгновенно удалено)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="gen_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_custom_duration)
async def process_custom_duration(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    try:
        d = int(message.text.strip())
        if d >= 0:
            await state.update_data(gen_duration=d)
    except Exception:
        pass

    await state.set_state(None)
    data = await state.get_data()
    prefix = data.get("gen_prefix", "PRO")
    count = data.get("gen_count", 5)
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "@Telegram")
    sample_key = data.get("sample_key", make_key(prefix))

    dur_display = "Бессрочная (Lifetime)" if duration == 0 else f"{duration} дней"
    text = (
        f"{PE_SPARKLES} <b>ГЕНЕРАТОР ЛИЦЕНЗИЙ // KEY GEN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_CHECK} <b>ЖИВОЙ ОБРАЗЕЦ КЛЮЧА:</b>\n"
        f"<code>{sample_key}</code>\n\n"
        f"<b>Параметры создаваемой партии:</b>\n"
        f"  {PE_TAG} Количество: <b>{count} шт.</b>\n"
        f"  {PE_DIAMOND} Префикс серии: <code>{prefix}-...</code>\n"
        f"  {PE_CLOCK} Срок действия: <b>{dur_display}</b>\n"
        f"  {PE_FILE} Примечание: <i>{note or '—'}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Нажмите на параметр для изменения или подтвердите создание:</i>"
    )
    kb = generator_keyboard(count, prefix, duration, note)
    await render_panel(message.chat.id, text, kb)

@dp.callback_query(F.data == "gen_prompt_note")
async def cb_gen_prompt_note(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_custom_note)
    text = (
        f"{PE_FILE} <b>ВВОД ПРИМЕЧАНИЯ К ПАРТИИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте текст заметки (например: <i>«Для клиента @user»</i> или <i>«Тест v2»</i>):\n"
        f"<i>(Ваше сообщение будет мгновенно удалено)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="gen_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_custom_note)
async def process_custom_note(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    nt = message.text.strip()[:60]
    await state.update_data(gen_note=nt)
    await state.set_state(None)

    data = await state.get_data()
    prefix = data.get("gen_prefix", "PRO")
    count = data.get("gen_count", 5)
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "@Telegram")
    sample_key = data.get("sample_key", make_key(prefix))

    dur_display = "Бессрочная (Lifetime)" if duration == 0 else f"{duration} дней"
    text = (
        f"{PE_SPARKLES} <b>ГЕНЕРАТОР ЛИЦЕНЗИЙ // KEY GEN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_CHECK} <b>ЖИВОЙ ОБРАЗЕЦ КЛЮЧА:</b>\n"
        f"<code>{sample_key}</code>\n\n"
        f"<b>Параметры создаваемой партии:</b>\n"
        f"  {PE_TAG} Количество: <b>{count} шт.</b>\n"
        f"  {PE_DIAMOND} Префикс серии: <code>{prefix}-...</code>\n"
        f"  {PE_CLOCK} Срок действия: <b>{dur_display}</b>\n"
        f"  {PE_FILE} Примечание: <i>{note or '—'}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Нажмите на параметр для изменения или подтвердите создание:</i>"
    )
    kb = generator_keyboard(count, prefix, duration, note)
    await render_panel(message.chat.id, text, kb)

# ВЫПОЛНЕНИЕ ГЕНЕРАЦИИ
@dp.callback_query(F.data == "gen_execute")
async def cb_gen_execute(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    count = data.get("gen_count", 5)
    prefix = data.get("gen_prefix", "PRO")
    duration = data.get("gen_duration", 30)
    note = data.get("gen_note", "TG Bot Generated")

    now_str = format_now()
    generated = []

    with get_db() as conn:
        c = conn.cursor()
        for _ in range(count):
            k = make_key(prefix)
            c.execute("""
                INSERT INTO licenses (key_code, status, duration_days, note, created_at)
                VALUES (?, 'available', ?, ?, ?)
            """, (k, duration, note, now_str))
            generated.append(k)
        conn.commit()

    # Сохраняем в память последние сгенерированные для скачивания
    await state.update_data(last_generated=generated)

    keys_formatted = "\n".join([f"• <code>{k}</code>" for k in generated[:15]])
    more_txt = f"\n<i>...и ещё {len(generated) - 15} ключей сохранено в базе</i>" if len(generated) > 15 else ""

    text = (
        f"{PE_CHECK} <b>УСПЕШНО СГЕНЕРИРОВАНО {count} КЛЮЧЕЙ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Параметры:</b> <code>{prefix}</code> | Срок: <b>{'Lifetime' if duration == 0 else f'{duration} дн.'}</b>\n"
        f"<b>Примечание:</b> <i>{note or '—'}</i>\n\n"
        f"<b>Список ключей (нажмите для копирования):</b>\n"
        f"{keys_formatted}{more_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Все ключи моментально синхронизированы с сайтом и базой SQLite!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скачать эту партию TXT", callback_data="download_last_gen", icon_custom_emoji_id=ID_DOWNLOAD)],
        [InlineKeyboardButton(text="Создать ещё ключи", callback_data="gen_menu", icon_custom_emoji_id=ID_NEW)],
        [InlineKeyboardButton(text="К списку всех ключей", callback_data="keys_list:all:0", icon_custom_emoji_id=ID_LIST)],
        [InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)],
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer("Партия ключей сгенерирована!")

@dp.callback_query(F.data == "download_last_gen")
async def cb_download_last_gen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keys = data.get("last_generated", [])
    if not keys:
        await callback.answer("Нет недавно сгенерированных ключей", show_alert=True)
        return

    content = "\n".join(keys)
    file = BufferedInputFile(content.encode("utf-8"), filename="batch_keys.txt")
    await bot.send_document(
        chat_id=callback.message.chat.id,
        document=file,
        caption=f"{PE_CHECK} Партия из <b>{len(keys)}</b> лицензионных ключей сформирована в .TXT"
    )
    await callback.answer("Файл отправлен!")

# =========================================================================
# 10. СПИСОК И УПРАВЛЕНИЕ ЛИЦЕНЗИЯМИ (СПИСОК, ФИЛЬТРЫ, ПАГИНАЦИЯ)
# =========================================================================
@dp.callback_query(F.data.startswith("keys_list:"))
async def cb_keys_list(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступно только админу", show_alert=True)
        return

    check_expired_licenses()
    parts = callback.data.split(":")
    status_filter = parts[1]
    page = int(parts[2])
    limit = 6
    offset = page * limit

    query = "SELECT * FROM licenses WHERE 1=1"
    params = []
    if status_filter != "all":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()

        count_query = "SELECT COUNT(*) FROM licenses WHERE 1=1"
        count_params = []
        if status_filter != "all":
            count_query += " AND status = ?"
            count_params.append(status_filter)
        c.execute(count_query, count_params)
        total_filtered = c.fetchone()[0]

    max_pages = (total_filtered + limit - 1) // limit if total_filtered > 0 else 1

    buttons = []
    # Вкладки фильтров как на сайте (Все, Свободные, Занятые, Заблокированные)
    filter_row = [
        InlineKeyboardButton(text=f"{'• ' if status_filter=='all' else ''}Все", callback_data="keys_list:all:0"),
        InlineKeyboardButton(text=f"{'• ' if status_filter=='available' else ''}Свободные", callback_data="keys_list:available:0"),
        InlineKeyboardButton(text=f"{'• ' if status_filter=='activated' else ''}Занятые", callback_data="keys_list:activated:0"),
        InlineKeyboardButton(text=f"{'• ' if status_filter=='blocked' else ''}Блок", callback_data="keys_list:blocked:0"),
    ]
    buttons.append(filter_row)

    # Список ключей
    for r in rows:
        st = r["status"]
        if st == "available":
            st_text = "Свободен"
            btn_icon = ID_LOCK
        elif st == "activated":
            st_text = "HWID Привязан"
            btn_icon = ID_USER
        elif st == "blocked":
            st_text = "Заблокирован"
            btn_icon = ID_CROSS
        else:
            st_text = "Истёк"
            btn_icon = ID_CLOCK

        buttons.append([InlineKeyboardButton(
            text=f"{r['key_code']} — {st_text}",
            callback_data=f"key_detail:{r['key_code']}",
            icon_custom_emoji_id=btn_icon
        )])

    # Строка навигации
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="Назад", callback_data=f"keys_list:{status_filter}:{page-1}", icon_custom_emoji_id=ID_BACK))
    nav_row.append(InlineKeyboardButton(text=f"Стр. {page+1}/{max_pages}", callback_data="noop"))
    if (page + 1) < max_pages:
        nav_row.append(InlineKeyboardButton(text="Вперед", callback_data=f"keys_list:{status_filter}:{page+1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="Поиск ключа", callback_data="search_prompt", icon_custom_emoji_id=ID_SEARCH),
        InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)
    ])

    filter_names = {
        "all": "ВСЕ ЛИЦЕНЗИИ",
        "available": "СВОБОДНЫЕ КЛЮЧИ",
        "activated": "АКТИВИРОВАННЫЕ (HWID)",
        "blocked": "ЗАБЛОКИРОВАННЫЕ",
        "expired": "ИСТЕКШИЕ"
    }

    text = (
        f"{PE_LIST} <b>УПРАВЛЕНИЕ БАЗОЙ ЛИЦЕНЗИЙ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Фильтр: <b>{filter_names.get(status_filter, status_filter.upper())}</b>\n"
        f"Всего по фильтру: <b>{total_filtered} шт.</b> | Страница: <b>{page+1} из {max_pages}</b>\n\n"
        f"<i>Нажмите на любой ключ для подробной карточки и управления:</i>"
    )
    await render_panel(callback.message.chat.id, text, InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

# ДЕТАЛЬНАЯ КАРТОЧКА ЛИЦЕНЗИИ
@dp.callback_query(F.data.startswith("key_detail:"))
async def cb_key_detail(callback: CallbackQuery):
    key_code = callback.data.split(":")[1]

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM licenses WHERE key_code = ?", (key_code,))
        row = c.fetchone()

    if not row:
        await callback.answer("Ключ не найден в базе!", show_alert=True)
        return

    st = row["status"]
    if st == "available":
        status_text = f"{PE_CHECK} <b>Свободен для ввода</b>"
    elif st == "activated":
        status_text = f"{PE_LIGHTNING} <b>Активирован (HWID привязан)</b>"
    elif st == "blocked":
        status_text = f"{PE_CROSS} <b>Заблокирован администратором</b>"
    else:
        status_text = f"{PE_CLOCK} <b>Срок действия истёк</b>"

    hwid_txt = f"<code>{row['hwid']}</code>" if row['hwid'] else "<i>Не привязан (пусто)</i>"
    dur_txt = "Бессрочная (Lifetime)" if row['duration_days'] == 0 else f"{row['duration_days']} дней"

    act_txt = f"  • Активирован: <code>{row['activated_at']}</code>\n" if row['activated_at'] else ""
    exp_txt = f"  • Истекает: <code>{row['expires_at']}</code>\n" if row['expires_at'] else ""

    text = (
        f"{PE_DIAMOND} <b>КАРТОЧКА ЛИЦЕНЗИОННОГО КЛЮЧА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Ключ:</b> <code>{row['key_code']}</code>\n"
        f"<b>Статус:</b> {status_text}\n"
        f"<b>Срок:</b> <b>{dur_txt}</b>\n"
        f"<b>HWID устройства:</b> {hwid_txt}\n"
        f"<b>Примечание:</b> <i>{row['note'] or '—'}</i>\n\n"
        f"<b>Хронология:</b>\n"
        f"  • Создан: <code>{row['created_at']}</code>\n"
        f"{act_txt}{exp_txt}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Быстрые действия над лицензией:</i>"
    )

    buttons = []
    actions_row = []

    # Кнопка сброса HWID (если ключ привязан)
    if row["hwid"]:
        actions_row.append(InlineKeyboardButton(
            text="Сбросить HWID",
            callback_data=f"key_reset_hwid:{key_code}",
            icon_custom_emoji_id=ID_REPEAT
        ))

    # Кнопка блокировки/разблокировки
    if st == "blocked":
        actions_row.append(InlineKeyboardButton(
            text="Разблокировать",
            callback_data=f"key_toggle_block:{key_code}",
            icon_custom_emoji_id=ID_UNLOCK
        ))
    else:
        actions_row.append(InlineKeyboardButton(
            text="Заблокировать",
            callback_data=f"key_toggle_block:{key_code}",
            icon_custom_emoji_id=ID_LOCK
        ))

    if actions_row:
        buttons.append(actions_row)

    buttons.append([
        InlineKeyboardButton(text="Изменить заметку", callback_data=f"key_edit_note:{key_code}", icon_custom_emoji_id=ID_EDIT),
        InlineKeyboardButton(text="Удалить ключ", callback_data=f"key_delete_direct:{key_code}", icon_custom_emoji_id=ID_TRASH)
    ])

    buttons.append([
        InlineKeyboardButton(text="К списку ключей", callback_data="keys_list:all:0", icon_custom_emoji_id=ID_BACK)
    ])

    await render_panel(callback.message.chat.id, text, InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("key_reset_hwid:"))
async def cb_key_reset_hwid(callback: CallbackQuery):
    key_code = callback.data.split(":")[1]
    with get_db() as conn:
        conn.execute("""
            UPDATE licenses 
            SET hwid = NULL, status = 'available', activated_at = NULL, expires_at = NULL 
            WHERE key_code = ?
        """, (key_code,))
        conn.commit()

    await callback.answer("HWID сброшен! Ключ снова готов к выдаче.", show_alert=True)
    await cb_key_detail(callback)

@dp.callback_query(F.data.startswith("key_toggle_block:"))
async def cb_key_toggle_block(callback: CallbackQuery):
    key_code = callback.data.split(":")[1]
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT status, hwid FROM licenses WHERE key_code = ?", (key_code,))
        r = c.fetchone()
        new_st = "blocked" if r["status"] != "blocked" else ("activated" if r["hwid"] else "available")
        conn.execute("UPDATE licenses SET status = ? WHERE key_code = ?", (new_st, key_code))
        conn.commit()

    await callback.answer(f"Статус изменен: {new_st}")
    await cb_key_detail(callback)

@dp.callback_query(F.data.startswith("key_delete_direct:"))
async def cb_key_delete_direct(callback: CallbackQuery):
    key_code = callback.data.split(":")[1]
    with get_db() as conn:
        conn.execute("DELETE FROM licenses WHERE key_code = ?", (key_code,))
        conn.commit()

    await callback.answer(f"Ключ {key_code} безвозвратно удален!")
    callback.data = "keys_list:all:0"
    await cb_keys_list(callback)

# Редактирование заметки конкретного ключа
@dp.callback_query(F.data.startswith("key_edit_note:"))
async def cb_key_edit_note(callback: CallbackQuery, state: FSMContext):
    key_code = callback.data.split(":")[1]
    await state.set_state(PanelStates.waiting_edit_note)
    await state.update_data(editing_key_code=key_code)

    text = (
        f"{PE_EDIT} <b>ИЗМЕНЕНИЕ ЗАМЕТКИ КЛЮЧА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Ключ: <code>{key_code}</code>\n\n"
        f"Отправьте в чат новый текст заметки:\n"
        f"<i>(Ваше сообщение будет мгновенно удалено)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=f"key_detail:{key_code}", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_edit_note)
async def process_key_edit_note(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    key_code = data.get("editing_key_code")
    new_note = message.text.strip()[:100]

    if key_code:
        with get_db() as conn:
            conn.execute("UPDATE licenses SET note = ? WHERE key_code = ?", (new_note, key_code))
            conn.commit()

    await state.set_state(None)
    # Возвращаемся в карточку ключа
    fake_query = CallbackQuery(
        id="0",
        from_user=message.from_user,
        chat_instance="0",
        message=message,
        data=f"key_detail:{key_code}"
    )
    await cb_key_detail(fake_query)

# =========================================================================
# 11. ПОИСК ПО БАЗЕ
# =========================================================================
@dp.callback_query(F.data == "search_prompt")
async def cb_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_search_query)

    text = (
        f"{PE_SEARCH} <b>ПОИСК КЛЮЧА В БАЗЕ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте сообщение с частью ключа, HWID или заметки для мгновенного поиска:\n\n"
        f"<i>(Ваше сообщение будет автоматически удалено, а результаты появятся здесь)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="to_main_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_search_query)
async def process_search_query(message: Message, state: FSMContext):
    q = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM licenses 
            WHERE key_code LIKE ? OR hwid LIKE ? OR note LIKE ?
            ORDER BY id DESC LIMIT 8
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = c.fetchall()

    await state.set_state(None)

    if not rows:
        res_text = (
            f"{PE_SEARCH} <b>РЕЗУЛЬТАТЫ ПОИСКА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"По запросу <code>{q}</code> ничего не найдено.\n"
            f"<i>Попробуйте ввести другой поисковый запрос.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Искать снова", callback_data="search_prompt", icon_custom_emoji_id=ID_SEARCH)],
            [InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)],
        ])
    else:
        res_text = (
            f"{PE_SEARCH} <b>РЕЗУЛЬТАТЫ ПОИСКА (Найдено {len(rows)}):</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Запрос: <code>{q}</code>\n\n"
            f"<i>Нажмите на ключ для перехода в карточку:</i>"
        )
        buttons = []
        for r in rows:
            st = r["status"]
            icon = ID_LOCK if st == "available" else (ID_USER if st == "activated" else ID_CROSS)
            buttons.append([InlineKeyboardButton(
                text=f"{r['key_code']} ({st})",
                callback_data=f"key_detail:{r['key_code']}",
                icon_custom_emoji_id=icon
            )])
        buttons.append([
            InlineKeyboardButton(text="Новый поиск", callback_data="search_prompt", icon_custom_emoji_id=ID_SEARCH),
            InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)
        ])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await render_panel(message.chat.id, res_text, kb)

# =========================================================================
# 12. СИМУЛЯТОР КЛИЕНТСКОГО ПК (ТЕСТЕР - ПОЛНЫЙ АНАЛОГ САЙТА!)
# =========================================================================
@dp.callback_query(F.data == "tester_menu")
async def cb_tester_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_hwid = data.get("test_hwid", f"HWID-PC-{uuid.uuid4().hex[:6].upper()}")
    test_key = data.get("test_key", "")
    terminal_log = data.get("terminal_log", "Ожидание команды активации или проверки...")

    await state.update_data(test_hwid=test_hwid, test_key=test_key, terminal_log=terminal_log)

    key_display = f"<code>{test_key}</code>" if test_key else "<i>Не выбран (введите или возьмите из базы)</i>"

    default_tpl = (
        f"{PE_DESKTOP} <b>СИМУЛЯТОР КЛИЕНТСКОГО ПК // TESTER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_LIGHTNING} <b>Виртуальный HWID ПК:</b> <code>{{test_hwid}}</code>\n"
        f"{PE_DIAMOND} <b>Тестовый ключ:</b> {{key_display}}\n\n"
        f"<b>TERMINAL // CLIENT_LOG:</b>\n"
        f"<code>{{terminal_log}}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите действие для тестирования:</i>"
    )
    raw_text = get_screen_text("tester_menu", default_tpl)
    try:
        text = raw_text.format(test_hwid=test_hwid, key_display=key_display, terminal_log=terminal_log)
    except Exception:
        text = raw_text

    kb = get_screen_keyboard("tester_menu")
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data == "tester_randomize_hwid")
async def cb_tester_randomize_hwid(callback: CallbackQuery, state: FSMContext):
    new_hwid = f"HWID-PC-{uuid.uuid4().hex[:6].upper()}"
    await state.update_data(
        test_hwid=new_hwid,
        terminal_log=f"[+] Сгенерирован новый виртуальный ПК:\nHWID: {new_hwid}"
    )
    await cb_tester_menu(callback, state)

@dp.callback_query(F.data == "tester_pick_free_key")
async def cb_tester_pick_free_key(callback: CallbackQuery, state: FSMContext):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT key_code FROM licenses WHERE status = 'available' ORDER BY id DESC LIMIT 1")
        row = c.fetchone()

    if not row:
        await callback.answer("В базе нет свободных ключей! Создайте их через генератор.", show_alert=True)
        return

    chosen = row[0]
    await state.update_data(
        test_key=chosen,
        terminal_log=f"[+] Из базы автоматически взят свободный ключ:\n{chosen}"
    )
    await callback.answer(f"Выбран ключ: {chosen}")
    await cb_tester_menu(callback, state)

@dp.callback_query(F.data == "tester_prompt_key")
async def cb_tester_prompt_key(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_test_key)
    text = (
        f"{PE_LIGHTNING} <b>ВВОД КЛЮЧА ДЛЯ ТЕСТИРОВАНИЯ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте боту ключ лицензии (например, <code>PRO-XXXX-XXXX-XXXX</code>):\n"
        f"<i>(Ваше сообщение будет мгновенно удалено)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="tester_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_test_key)
async def process_test_key_input(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    k = message.text.strip().upper()
    await state.update_data(test_key=k, terminal_log=f"[+] Введен ключ для теста: {k}")
    await state.set_state(None)

    fake_query = CallbackQuery(
        id="0",
        from_user=message.from_user,
        chat_instance="0",
        message=message,
        data="tester_menu"
    )
    await cb_tester_menu(fake_query, state)

@dp.callback_query(F.data == "tester_prompt_hwid")
async def cb_tester_prompt_hwid(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_test_hwid)
    text = (
        f"{PE_DESKTOP} <b>ВВОД КАСТОМНОГО HWID</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте желаемый HWID (например, <code>MY-CUSTOM-PC-123</code>):\n"
        f"<i>(Ваше сообщение будет мгновенно удалено)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="tester_menu", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_test_hwid)
async def process_test_hwid_input(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    h = message.text.strip()
    await state.update_data(test_hwid=h, terminal_log=f"[+] Установлен кастомный HWID: {h}")
    await state.set_state(None)

    fake_query = CallbackQuery(
        id="0",
        from_user=message.from_user,
        chat_instance="0",
        message=message,
        data="tester_menu"
    )
    await cb_tester_menu(fake_query, state)

# СИМУЛЯЦИЯ 1. АКТИВАЦИИ
@dp.callback_query(F.data == "tester_exec_activate")
async def cb_tester_exec_activate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hwid = data.get("test_hwid", "HWID-TEST-PC")
    key = data.get("test_key", "").strip()

    if not key:
        await callback.answer("Сначала введите ключ или нажмите «Взять ключ из базы»!", show_alert=True)
        return

    now_str = format_now()

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM licenses WHERE key_code = ?", (key,))
        row = c.fetchone()

        # СТРОГАЯ ПРОВЕРКА КЛИЕНТА (как в app.py)
        if not row:
            log = f"[POST /api/client/activate] -> 404 NOT FOUND\nОшибка: Неверный ключ доступа."
        elif row["status"] == "blocked":
            log = f"[POST /api/client/activate] -> 403 FORBIDDEN\nОшибка: Этот ключ заблокирован администратором."
        elif row["status"] == "expired":
            log = f"[POST /api/client/activate] -> 403 FORBIDDEN\nОшибка: Срок действия ключа истек."
        elif row["status"] == "activated":
            if row["hwid"] == hwid:
                log = (
                    f"[POST /api/client/activate] -> 200 OK\n"
                    f"Ключ уже активирован на данном ПК ({hwid}).\n"
                    f"Доступ предоставлен."
                )
            else:
                log = (
                    f"[POST /api/client/activate] -> 409 CONFLICT!\n"
                    f"ОШИБКА: Ключ уже активирован на ДРУГОМ устройстве:\n"
                    f"[{row['hwid']}]\n"
                    f"Повторное использование строго запрещено!"
                )
        else:
            # Успешная первичная активация
            expires_at_str = None
            dur = row["duration_days"]
            if dur > 0:
                exp_dt = datetime.utcnow() + timedelta(days=dur)
                expires_at_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

            c.execute("""
                UPDATE licenses 
                SET status = 'activated', hwid = ?, activated_at = ?, expires_at = ?
                WHERE key_code = ?
            """, (hwid, now_str, expires_at_str, key))
            conn.commit()

            log = (
                f"[POST /api/client/activate] -> 200 OK\n"
                f"УСПЕХ: Ключ успешно активирован и привязан к железу!\n"
                f"HWID: {hwid}\n"
                f"Срок: {'Lifetime' if dur==0 else f'{dur} дн. (до {expires_at_str})'}"
            )

    await state.update_data(terminal_log=log)
    await cb_tester_menu(callback, state)

# СИМУЛЯЦИЯ 2. ПРОВЕРКИ ДОСТУПА (VERIFY)
@dp.callback_query(F.data == "tester_exec_verify")
async def cb_tester_exec_verify(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hwid = data.get("test_hwid", "HWID-TEST-PC")

    now_str = format_now()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM licenses WHERE hwid = ? AND status = 'activated'", (hwid,))
        row = c.fetchone()

        if not row:
            log = (
                f"[POST /api/client/verify] -> 200 OK (valid: false)\n"
                f"Для ПК [{hwid}] нет активной лицензии.\n"
                f"Требуется ввести ключ."
            )
        else:
            if row["expires_at"] and row["expires_at"] < now_str:
                c.execute("UPDATE licenses SET status = 'expired' WHERE id = ?", (row["id"],))
                conn.commit()
                log = (
                    f"[POST /api/client/verify] -> 200 OK (valid: false)\n"
                    f"Лицензия истекла! Срок действия окончен ({row['expires_at']})."
                )
            else:
                dur_text = "Lifetime" if row["duration_days"] == 0 else f"до {row['expires_at']}"
                log = (
                    f"[POST /api/client/verify] -> 200 OK (valid: true)\n"
                    f"Лицензия действительна!\n"
                    f"Ключ: {row['key_code']}\n"
                    f"Срок: {dur_text}"
                )

    await state.update_data(terminal_log=log)
    await cb_tester_menu(callback, state)

# =========================================================================
# 13. ЭКСПОРТ В TXT (В ОДНОМ СООБЩЕНИИ + ОТПРАВКА ФАЙЛА)
# =========================================================================
@dp.callback_query(F.data == "export_menu")
async def cb_export_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступно только админу", show_alert=True)
        return

    text = get_screen_text("export_menu")
    kb = get_screen_keyboard("export_menu")
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data.in_(["export_run", "export_send_file"]))
async def cb_export_send_file(callback: CallbackQuery):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT key_code FROM licenses WHERE status = 'available' ORDER BY id DESC")
        keys = [r[0] for r in c.fetchall()]

    if not keys:
        await callback.answer("Нет свободных ключей!", show_alert=True)
        return

    content = f"# KeyPulse License Keys Export\n# Total: {len(keys)}\n# Generated: {format_now()} UTC\n\n"
    content += "\n".join(keys)

    file = BufferedInputFile(content.encode("utf-8"), filename="available_keys.txt")
    await bot.send_document(
        chat_id=callback.message.chat.id,
        document=file,
        caption=f"{PE_CHECK} Экспортировано <b>{len(keys)}</b> свободных ключей."
    )
    await callback.answer("Файл отправлен в чат!")

# =========================================================================
# 14. ПОЛЬЗОВАТЕЛЬСКИЙ РАЗДЕЛ (АКТИВАЦИЯ И СТАТУС ДЛЯ КЛИЕНТОВ)
# =========================================================================
@dp.callback_query(F.data == "user_activate_prompt")
async def cb_user_activate_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PanelStates.waiting_key_activate)
    text = get_screen_text("user_activate_prompt")
    kb = get_screen_keyboard("user_activate_prompt")
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.waiting_key_activate)
async def process_user_key_activation(message: Message, state: FSMContext):
    key_input = message.text.strip().upper()
    user_hwid = f"TG-USER-{message.from_user.id}"
    now_str = format_now()

    # Сразу удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM licenses WHERE key_code = ?", (key_input,))
        row = c.fetchone()

        if not row:
            res_text = (
                f"{PE_CROSS} <b>ОШИБКА АКТИВАЦИИ</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Ключ <code>{key_input}</code> не найден в базе данных.\n"
                f"Проверьте правильность написания и попробуйте снова."
            )
        elif row["status"] == "blocked":
            res_text = (
                f"{PE_CROSS} <b>ОШИБКА ДОСТУПА</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Ключ <code>{key_input}</code> заблокирован администратором."
            )
        elif row["status"] == "expired":
            res_text = (
                f"{PE_CLOCK} <b>СРОК ИСТЕК</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Срок действия ключа <code>{key_input}</code> подошел к концу."
            )
        elif row["status"] == "activated":
            if row["hwid"] == user_hwid:
                res_text = (
                    f"{PE_CHECK} <b>ЛИЦЕНЗИЯ УЖЕ АКТИВНА</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Ключ <code>{key_input}</code> уже привязан к вашему аккаунту!\n"
                    f"Доступ предоставлен."
                )
            else:
                res_text = (
                    f"{PE_CROSS} <b>ОШИБКА 409 CONFLICT!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Этот ключ уже активирован другим пользователем или на другом устройстве.\n"
                    f"Повторное использование лицензии невозможно!"
                )
        else:
            # Успешная активация
            dur = row["duration_days"]
            exp_str = None
            if dur > 0:
                exp_dt = datetime.utcnow() + timedelta(days=dur)
                exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

            c.execute("""
                UPDATE licenses 
                SET status = 'activated', hwid = ?, activated_at = ?, expires_at = ?
                WHERE key_code = ?
            """, (user_hwid, now_str, exp_str, key_input))
            conn.commit()

            dur_text = "Бессрочная (Lifetime)" if dur == 0 else f"{dur} дней (до {exp_str})"
            res_text = (
                f"{PE_CHECK} <b>УСПЕШНАЯ АКТИВАЦИЯ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Лицензия: <code>{key_input}</code>\n"
                f"Тариф: <b>{dur_text}</b>\n"
                f"Привязка: <code>{user_hwid}</code>\n"
                f"Дата активации: <code>{now_str}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Все функции приложения успешно разблокированы!</i>"
            )

    await state.set_state(None)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Моя лицензия", callback_data="user_my_status", icon_custom_emoji_id=ID_USER)],
        [InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)],
    ])
    await render_panel(message.chat.id, res_text, kb)

@dp.callback_query(F.data == "user_my_status")
async def cb_user_my_status(callback: CallbackQuery):
    user_hwid = f"TG-USER-{callback.from_user.id}"
    check_expired_licenses()

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM licenses WHERE hwid = ? AND status = 'activated'", (user_hwid,))
        row = c.fetchone()

    if row:
        dur = "Бессрочная (Lifetime)" if row['duration_days'] == 0 else f"{row['duration_days']} дней"
        exp = f"  • Действует до: <code>{row['expires_at']}</code>\n" if row['expires_at'] else ""
        text = (
            f"{PE_CHECK} <b>ВАША АКТИВНАЯ ЛИЦЕНЗИЯ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Ключ:</b> <code>{row['key_code']}</code>\n"
            f"<b>Тариф:</b> <b>{dur}</b>\n"
            f"<b>Статус:</b> <b>Активна (Full Access)</b>\n\n"
            f"<b>Информация:</b>\n"
            f"  • Активирована: <code>{row['activated_at']}</code>\n"
            f"{exp}"
            f"  • ID пользователя: <code>{user_hwid}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = get_screen_text("user_my_status")
        kb = get_screen_keyboard("user_my_status")
        await render_panel(callback.message.chat.id, text, kb)
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Активировать ключ", callback_data="user_activate_prompt", icon_custom_emoji_id=ID_LOCK)],
        [InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)],
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data == "about_info")
async def cb_about_info(callback: CallbackQuery):
    text = get_screen_text("about_info")
    kb = get_screen_keyboard("about_info")
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("screen:"))
async def cb_open_custom_screen(callback: CallbackQuery):
    screen_key = callback.data.split("screen:", 1)[1]
    text = get_screen_text(screen_key)
    if not text:
        await callback.answer("Раздел не найден или удален.", show_alert=True)
        return
    kb = get_screen_keyboard(screen_key)
    if not kb.inline_keyboard:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK)]
        ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

# =========================================================================
# 15. КОНСТРУКТОР БОТА (UI BUILDER / CMS ДЛЯ СООБЩЕНИЙ И КНОПОК)
# =========================================================================
async def render_constructor_main(chat_id: int):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT screen_key, title, is_system FROM bot_screens ORDER BY is_system DESC, title ASC")
        screens = c.fetchall()

    text = (
        f"{PE_GEAR} <b>КОНСТРУКТОР БОТА // UI BUILDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Полный визуальный редактор интерфейса бота.\n\n"
        f"• <b>Тексты:</b> Редактируйте любые сообщения, HTML и переменные.\n"
        f"• <b>Кнопки:</b> Добавляйте, удаляйте, меняйте текст и ссылки.\n"
        f"• <b>Эмодзи:</b> Устанавливайте любые премиум-эмодзи на кнопки.\n"
        f"• <b>Экраны:</b> Создавайте свои собственные разделы меню.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите экран для настройки:</i>"
    )

    kb_rows = []
    row = []
    for s in screens:
        icon = ID_FILE if s["is_system"] else ID_SPARKLES
        row.append(InlineKeyboardButton(text=s["title"], callback_data=f"cns_scr:{s['screen_key']}", icon_custom_emoji_id=icon))
        if len(row) == 2:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    kb_rows.append([
        InlineKeyboardButton(text="Создать новый экран", callback_data="cns_new_scr", icon_custom_emoji_id=ID_NEW),
    ])
    kb_rows.append([
        InlineKeyboardButton(text="В главное меню", callback_data="to_main_menu", icon_custom_emoji_id=ID_BACK),
    ])

    await render_panel(chat_id, text, InlineKeyboardMarkup(inline_keyboard=kb_rows))

async def render_screen_editor(chat_id: int, screen_key: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM bot_screens WHERE screen_key = ?", (screen_key,))
        scr = c.fetchone()
        c.execute("SELECT * FROM bot_buttons WHERE screen_key = ? ORDER BY row_index ASC, sort_order ASC, id ASC", (screen_key,))
        btns = c.fetchall()

    if not scr:
        return

    raw_text = scr["message_text"]
    preview_text = raw_text if len(raw_text) <= 400 else raw_text[:397] + "..."

    if btns:
        btn_lines = []
        for i, b in enumerate(btns, 1):
            emj_info = f"[Эмодзи ID: {b['icon_emoji_id']}] " if b['icon_emoji_id'] else ""
            act_info = f"({b['action_type']}: {b['action_value']})"
            btn_lines.append(f"<b>{i}.</b> {emj_info}«{b['btn_text']}» -> <code>{act_info}</code> [Ряд {b['row_index']+1}]")
        btn_summary = "\n".join(btn_lines)
    else:
        btn_summary = "<i>Кнопок нет (пусто)</i>"

    is_sys_str = "Системный экран" if scr["is_system"] else "Кастомный экран"

    text = (
        f"{PE_SLIDERS} <b>РЕДАКТОР ЭКРАНА:</b> {scr['title']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ID Экрана:</b> <code>{screen_key}</code> ({is_sys_str})\n\n"
        f"<b>ТЕКУЩИЙ ТЕКСТ СООБЩЕНИЯ:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{preview_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>КНОПКИ НА ЭКРАНЕ ({len(btns)} шт.):</b>\n"
        f"{btn_summary}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите действие для этого экрана:</i>"
    )

    kb_rows = [
        [
            InlineKeyboardButton(text="Изменить текст", callback_data=f"cns_edt_txt:{screen_key}", icon_custom_emoji_id=ID_EDIT),
            InlineKeyboardButton(text="Управление кнопками", callback_data=f"cns_btns:{screen_key}", icon_custom_emoji_id=ID_LIST),
        ],
        [
            InlineKeyboardButton(text="Добавить кнопку", callback_data=f"cns_add_btn:{screen_key}", icon_custom_emoji_id=ID_NEW),
        ],
    ]

    if scr["is_system"]:
        kb_rows.append([
            InlineKeyboardButton(text="Сбросить к умолчанию", callback_data=f"cns_reset:{screen_key}", icon_custom_emoji_id=ID_REPEAT),
        ])
    else:
        kb_rows.append([
            InlineKeyboardButton(text="УДАЛИТЬ ЭТОТ ЭКРАН", callback_data=f"cns_del_scr:{screen_key}", icon_custom_emoji_id=ID_TRASH),
        ])

    kb_rows.append([
        InlineKeyboardButton(text="Назад в Конструктор", callback_data="cns_main", icon_custom_emoji_id=ID_BACK),
    ])

    await render_panel(chat_id, text, InlineKeyboardMarkup(inline_keyboard=kb_rows))

async def render_screen_buttons_list(chat_id: int, screen_key: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT title FROM bot_screens WHERE screen_key = ?", (screen_key,))
        scr = c.fetchone()
        c.execute("SELECT * FROM bot_buttons WHERE screen_key = ? ORDER BY row_index ASC, sort_order ASC, id ASC", (screen_key,))
        btns = c.fetchall()

    title = scr["title"] if scr else screen_key

    text = (
        f"{PE_LIST} <b>КНОПКИ ЭКРАНА:</b> {title}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Нажмите на любую кнопку ниже, чтобы настроить её:\n"
        f"• Изменить текст\n"
        f"• Назначить премиум-эмодзи\n"
        f"• Изменить действие или ссылку\n"
        f"• Переместить по строкам\n"
        f"• Удалить кнопку\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    kb_rows = []
    for b in btns:
        kw = {"text": f"[{b['row_index']+1} ряд] {b['btn_text']}", "callback_data": f"cns_btn_v:{b['id']}"}
        if b["icon_emoji_id"] and str(b["icon_emoji_id"]).strip():
            kw["icon_custom_emoji_id"] = str(b["icon_emoji_id"]).strip()
        kb_rows.append([InlineKeyboardButton(**kw)])

    kb_rows.append([
        InlineKeyboardButton(text="Добавить кнопку", callback_data=f"cns_add_btn:{screen_key}", icon_custom_emoji_id=ID_NEW),
    ])
    kb_rows.append([
        InlineKeyboardButton(text="Назад к экрану", callback_data=f"cns_scr:{screen_key}", icon_custom_emoji_id=ID_BACK),
    ])

    await render_panel(chat_id, text, InlineKeyboardMarkup(inline_keyboard=kb_rows))

async def render_button_detail(chat_id: int, btn_id: int):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM bot_buttons WHERE id = ?", (btn_id,))
        b = c.fetchone()

    if not b:
        return

    emj_str = f"<code>{b['icon_emoji_id']}</code>" if b["icon_emoji_id"] else "<i>Без премиум-эмодзи</i>"
    act_str = f"<b>{b['action_type'].upper()}</b> -> <code>{b['action_value']}</code>"

    text = (
        f"{PE_GEAR} <b>НАСТРОЙКА КНОПКИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Экран:</b> <code>{b['screen_key']}</code>\n"
        f"<b>Текст кнопки:</b> <b>{b['btn_text']}</b>\n"
        f"<b>Премиум-эмодзи:</b> {emj_str}\n"
        f"<b>Действие:</b> {act_str}\n"
        f"<b>Строка (ряд):</b> <b>{b['row_index'] + 1}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите параметр для изменения:</i>"
    )

    kb_rows = [
        [
            InlineKeyboardButton(text="Изменить текст", callback_data=f"cns_b_txt:{btn_id}", icon_custom_emoji_id=ID_EDIT),
            InlineKeyboardButton(text="Выбрать эмодзи", callback_data=f"cns_b_emj:{btn_id}", icon_custom_emoji_id=ID_STAR),
        ],
        [
            InlineKeyboardButton(text="Ввести свой Emoji ID", callback_data=f"cns_b_cust_emj:{btn_id}", icon_custom_emoji_id=ID_TAG),
            InlineKeyboardButton(text="Убрать эмодзи", callback_data=f"cns_b_clr_emj:{btn_id}", icon_custom_emoji_id=ID_CROSS),
        ],
        [
            InlineKeyboardButton(text="Изменить действие/ссылку", callback_data=f"cns_b_act:{btn_id}", icon_custom_emoji_id=ID_DIAMOND),
        ],
        [
            InlineKeyboardButton(text="В новую строку (Ряд +1)", callback_data=f"cns_b_row_inc:{btn_id}", icon_custom_emoji_id=ID_REPEAT),
            InlineKeyboardButton(text="В строку выше (Ряд -1)", callback_data=f"cns_b_row_dec:{btn_id}", icon_custom_emoji_id=ID_REPEAT),
        ],
        [
            InlineKeyboardButton(text="УДАЛИТЬ КНОПКУ", callback_data=f"cns_b_del:{btn_id}", icon_custom_emoji_id=ID_TRASH),
        ],
        [
            InlineKeyboardButton(text="Назад к кнопкам", callback_data=f"cns_btns:{b['screen_key']}", icon_custom_emoji_id=ID_BACK),
        ]
    ]

    await render_panel(chat_id, text, InlineKeyboardMarkup(inline_keyboard=kb_rows))

@dp.callback_query(F.data == "cns_main")
async def cb_cns_main(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступно только администратору!", show_alert=True)
        return
    await state.clear()
    await render_constructor_main(callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_scr:"))
async def cb_cns_screen_detail(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    screen_key = callback.data.split("cns_scr:", 1)[1]
    await render_screen_editor(callback.message.chat.id, screen_key)
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_edt_txt:"))
async def cb_cns_edit_text_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    screen_key = callback.data.split("cns_edt_txt:", 1)[1]
    await state.set_state(PanelStates.cns_edit_text)
    await state.update_data(cns_screen_key=screen_key)

    cur_text = get_screen_text(screen_key)

    text = (
        f"{PE_EDIT} <b>ИЗМЕНЕНИЕ ТЕКСТА ЭКРАНА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ID Экрана:</b> <code>{screen_key}</code>\n\n"
        f"Отправьте в чат новый текст для этого сообщения.\n"
        f"• Поддерживается форматирование Telegram HTML (<b>жирный</b>, <i>курсив</i>, <code>код</code>).\n"
        f"• Поддерживаются премиум-эмодзи: <code>&lt;tg-emoji emoji-id=\"ID\"&gt;icon&lt;/tg-emoji&gt;</code>\n"
        f"• Переменные (для нужных экранов): <code>{{user_name}}</code>, <code>{{stats_total}}</code> и т.д.\n\n"
        f"<i>Текущий текст отправлен ниже для удобного копирования и редактирования:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=f"cns_scr:{screen_key}", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    try:
        sent_draft = await callback.message.answer(f"<code>{cur_text}</code>", parse_mode=ParseMode.HTML)
        await state.update_data(cns_draft_msg_id=sent_draft.message_id)
    except Exception:
        pass
    await callback.answer()

@dp.message(PanelStates.cns_edit_text)
async def process_cns_edit_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    screen_key = data.get("cns_screen_key")
    draft_msg_id = data.get("cns_draft_msg_id")

    new_text = message.text or message.caption or ""

    try:
        await message.delete()
    except Exception:
        pass

    if draft_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=draft_msg_id)
        except Exception:
            pass

    if screen_key and new_text:
        now_str = format_now()
        with get_db() as conn:
            conn.execute("""
                UPDATE bot_screens 
                SET message_text = ?, updated_at = ? 
                WHERE screen_key = ?
            """, (new_text, now_str, screen_key))
            conn.commit()

    await state.clear()
    await render_screen_editor(message.chat.id, screen_key)

@dp.callback_query(F.data.startswith("cns_reset:"))
async def cb_cns_reset_screen(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    screen_key = callback.data.split("cns_reset:", 1)[1]
    reset_screen_to_default(screen_key)
    await callback.answer("Экран сброшен к исходным настройкам!", show_alert=True)
    await render_screen_editor(callback.message.chat.id, screen_key)

@dp.callback_query(F.data.startswith("cns_btns:"))
async def cb_cns_buttons_list(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    screen_key = callback.data.split("cns_btns:", 1)[1]
    await render_screen_buttons_list(callback.message.chat.id, screen_key)
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_btn_v:"))
async def cb_cns_button_view(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    btn_id = int(callback.data.split("cns_btn_v:", 1)[1])
    await render_button_detail(callback.message.chat.id, btn_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_b_emj:"))
async def cb_cns_btn_emoji_gallery(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_emj:", 1)[1])

    text = (
        f"{PE_STAR} <b>ВЫБОР ПРЕМИУМ-ЭМОДЗИ ДЛЯ КНОПКИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Нажмите на любой премиум-значок ниже, чтобы установить его на кнопку:\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    kb_rows = []
    chunk = []
    for char, name, eid in EMOJI_GALLERY:
        chunk.append(InlineKeyboardButton(text=name, callback_data=f"cns_set_emj:{btn_id}:{eid}", icon_custom_emoji_id=eid))
        if len(chunk) == 3:
            kb_rows.append(chunk)
            chunk = []
    if chunk:
        kb_rows.append(chunk)

    kb_rows.append([
        InlineKeyboardButton(text="Назад к кнопке", callback_data=f"cns_btn_v:{btn_id}", icon_custom_emoji_id=ID_BACK)
    ])

    await render_panel(callback.message.chat.id, text, InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_set_emj:"))
async def cb_cns_set_emoji(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    parts = callback.data.split(":")
    btn_id = int(parts[1])
    emoji_id = parts[2]

    with get_db() as conn:
        conn.execute("UPDATE bot_buttons SET icon_emoji_id = ? WHERE id = ?", (emoji_id, btn_id))
        conn.commit()

    await callback.answer("Эмодзи успешно установлен!", show_alert=True)
    await render_button_detail(callback.message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_clr_emj:"))
async def cb_cns_clear_emoji(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_clr_emj:", 1)[1])
    with get_db() as conn:
        conn.execute("UPDATE bot_buttons SET icon_emoji_id = '' WHERE id = ?", (btn_id,))
        conn.commit()
    await callback.answer("Эмодзи удален с кнопки!", show_alert=True)
    await render_button_detail(callback.message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_cust_emj:"))
async def cb_cns_prompt_custom_emoji(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_cust_emj:", 1)[1])
    await state.set_state(PanelStates.cns_btn_custom_emoji)
    await state.update_data(cns_btn_id=btn_id)

    text = (
        f"{PE_EDIT} <b>ВВОД ID ПРЕМИУМ-ЭМОДЗИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте боту числовой ID премиум-эмодзи (например: <code>5805553606635559688</code>):\n"
        f"<i>(Вы можете скопировать ID любого эмодзи из Telegram или сайта emoji.wivvi.net)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=f"cns_btn_v:{btn_id}", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.cns_btn_custom_emoji)
async def process_cns_custom_emoji(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    btn_id = data.get("cns_btn_id")
    raw_id = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    if btn_id and raw_id:
        with get_db() as conn:
            conn.execute("UPDATE bot_buttons SET icon_emoji_id = ? WHERE id = ?", (raw_id, btn_id))
            conn.commit()

    await state.clear()
    await render_button_detail(message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_txt:"))
async def cb_cns_prompt_btn_text(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_txt:", 1)[1])
    await state.set_state(PanelStates.cns_btn_edit_text)
    await state.update_data(cns_btn_id=btn_id)

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT btn_text FROM bot_buttons WHERE id = ?", (btn_id,))
        row = c.fetchone()
    cur_text = row["btn_text"] if row else ""

    text = (
        f"{PE_EDIT} <b>ИЗМЕНЕНИЕ НАЗВАНИЯ КНОПКИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Текущее название: <b>{cur_text}</b>\n\n"
        f"Отправьте новое название кнопки в чат:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=f"cns_btn_v:{btn_id}", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.cns_btn_edit_text)
async def process_cns_btn_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    btn_id = data.get("cns_btn_id")
    new_txt = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    if btn_id and new_txt:
        with get_db() as conn:
            conn.execute("UPDATE bot_buttons SET btn_text = ? WHERE id = ?", (new_txt, btn_id))
            conn.commit()

    await state.clear()
    await render_button_detail(message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_act:"))
async def cb_cns_prompt_btn_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_act:", 1)[1])
    await state.set_state(PanelStates.cns_btn_edit_action)
    await state.update_data(cns_btn_id=btn_id)

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT action_type, action_value FROM bot_buttons WHERE id = ?", (btn_id,))
        row = c.fetchone()
    cur_val = f"{row['action_type'].upper()}: {row['action_value']}" if row else ""

    text = (
        f"{PE_DIAMOND} <b>ИЗМЕНЕНИЕ ДЕЙСТВИЯ КНОПКИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Текущее действие: <code>{cur_val}</code>\n\n"
        f"<b>Как настроить:</b>\n"
        f"• <b>Интернет-ссылка:</b> отправьте ссылку в чат (например: <code>https://t.me/mychannel</code>)\n"
        f"• <b>Кастомный экран:</b> отправьте в чат <code>screen:имя_экрана</code>\n"
        f"• Или выберите один из системных переходов ниже:\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="В главное меню", callback_data=f"cns_set_act:{btn_id}:callback:to_main_menu"),
            InlineKeyboardButton(text="Ввод ключа", callback_data=f"cns_set_act:{btn_id}:callback:user_activate_prompt"),
        ],
        [
            InlineKeyboardButton(text="Моя лицензия", callback_data=f"cns_set_act:{btn_id}:callback:user_my_status"),
            InlineKeyboardButton(text="О системе", callback_data=f"cns_set_act:{btn_id}:callback:about_info"),
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data=f"cns_btn_v:{btn_id}", icon_custom_emoji_id=ID_CROSS),
        ]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("cns_set_act:"))
async def cb_cns_set_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    parts = callback.data.split(":")
    btn_id = int(parts[1])
    act_type = parts[2]
    act_value = ":".join(parts[3:])

    with get_db() as conn:
        conn.execute("UPDATE bot_buttons SET action_type = ?, action_value = ? WHERE id = ?", (act_type, act_value, btn_id))
        conn.commit()

    await state.clear()
    await callback.answer("Действие кнопки обновлено!", show_alert=True)
    await render_button_detail(callback.message.chat.id, btn_id)

@dp.message(PanelStates.cns_btn_edit_action)
async def process_cns_btn_action(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    btn_id = data.get("cns_btn_id")
    raw = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    if btn_id and raw:
        act_type = "url" if (raw.startswith("http://") or raw.startswith("https://")) else "callback"
        with get_db() as conn:
            conn.execute("UPDATE bot_buttons SET action_type = ?, action_value = ? WHERE id = ?", (act_type, raw, btn_id))
            conn.commit()

    await state.clear()
    await render_button_detail(message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_row_inc:"))
async def cb_cns_row_inc(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_row_inc:", 1)[1])
    with get_db() as conn:
        conn.execute("UPDATE bot_buttons SET row_index = row_index + 1 WHERE id = ?", (btn_id,))
        conn.commit()
    await callback.answer("Кнопка перенесена на строку ниже!")
    await render_button_detail(callback.message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_row_dec:"))
async def cb_cns_row_dec(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_row_dec:", 1)[1])
    with get_db() as conn:
        conn.execute("UPDATE bot_buttons SET row_index = MAX(0, row_index - 1) WHERE id = ?", (btn_id,))
        conn.commit()
    await callback.answer("Кнопка перенесена на строку выше!")
    await render_button_detail(callback.message.chat.id, btn_id)

@dp.callback_query(F.data.startswith("cns_b_del:"))
async def cb_cns_delete_button(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    btn_id = int(callback.data.split("cns_b_del:", 1)[1])
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT screen_key FROM bot_buttons WHERE id = ?", (btn_id,))
        row = c.fetchone()
        screen_key = row["screen_key"] if row else "admin_main"
        conn.execute("DELETE FROM bot_buttons WHERE id = ?", (btn_id,))
        conn.commit()

    await callback.answer("Кнопка удалена!", show_alert=True)
    await render_screen_buttons_list(callback.message.chat.id, screen_key)

@dp.callback_query(F.data.startswith("cns_add_btn:"))
async def cb_cns_add_btn_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    screen_key = callback.data.split("cns_add_btn:", 1)[1]
    await state.set_state(PanelStates.cns_btn_new_text)
    await state.update_data(cns_screen_key=screen_key)

    text = (
        f"{PE_NEW} <b>ДОБАВЛЕНИЕ НОВОЙ КНОПКИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Экран назначения:</b> <code>{screen_key}</code>\n\n"
        f"Отправьте в чат название кнопки (например: <code>💬 Поддержка</code> или <code>🔥 Купить PRO</code>):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data=f"cns_btns:{screen_key}", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.cns_btn_new_text)
async def process_cns_new_btn_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    btn_txt = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass
    await state.update_data(cns_new_btn_title=btn_txt)
    await state.set_state(PanelStates.cns_btn_new_action)

    data = await state.get_data()
    screen_key = data.get("cns_screen_key")

    text = (
        f"{PE_DIAMOND} <b>ШАГ 2: ДЕЙСТВИЕ ДЛЯ КНОПКИ «{btn_txt}»</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Отправьте в чат:\n"
        f"• Ссылку в интернете: <code>https://t.me/username</code>\n"
        f"• Или экран: <code>screen:имя_экрана</code>\n\n"
        f"Или выберите готовое действие ниже:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="В главное меню", callback_data="cns_pick_act:to_main_menu"),
            InlineKeyboardButton(text="Ввод ключа", callback_data="cns_pick_act:user_activate_prompt"),
        ],
        [
            InlineKeyboardButton(text="Моя лицензия", callback_data="cns_pick_act:user_my_status"),
            InlineKeyboardButton(text="О системе", callback_data="cns_pick_act:about_info"),
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data=f"cns_btns:{screen_key}", icon_custom_emoji_id=ID_CROSS),
        ]
    ])
    await render_panel(message.chat.id, text, kb)

@dp.callback_query(F.data.startswith("cns_pick_act:"))
async def cb_cns_picked_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    act_val = callback.data.split("cns_pick_act:", 1)[1]
    await finalize_new_button(callback.message.chat.id, state, "callback", act_val)
    await callback.answer()

@dp.message(PanelStates.cns_btn_new_action)
async def process_cns_new_btn_action(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    raw = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass
    act_type = "url" if (raw.startswith("http://") or raw.startswith("https://")) else "callback"
    await finalize_new_button(message.chat.id, state, act_type, raw)

async def finalize_new_button(chat_id: int, state: FSMContext, act_type: str, act_val: str):
    data = await state.get_data()
    screen_key = data.get("cns_screen_key")
    btn_title = data.get("cns_new_btn_title", "Кнопка")

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COALESCE(MAX(row_index), 0) FROM bot_buttons WHERE screen_key = ?", (screen_key,))
        max_row = c.fetchone()[0]
        c.execute("""
            INSERT INTO bot_buttons (screen_key, btn_text, icon_emoji_id, action_type, action_value, row_index, col_index, is_active, sort_order)
            VALUES (?, ?, '', ?, ?, ?, 0, 1, 999)
        """, (screen_key, btn_title, act_type, act_val, max_row + 1))
        new_id = c.lastrowid
        conn.commit()

    await state.clear()
    await render_button_detail(chat_id, new_id)

@dp.callback_query(F.data == "cns_new_scr")
async def cb_cns_new_screen_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(PanelStates.cns_new_screen_key)

    text = (
        f"{PE_NEW} <b>СОЗДАНИЕ НОВОГО ЭКРАНА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Шаг 1 из 3:</b> Введите уникальный ID экрана на английском (например: <code>faq</code>, <code>rules</code>, <code>support</code>):\n\n"
        f"<i>(Этот ID будет использоваться в кнопках как <code>screen:имя</code>)</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cns_main", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(callback.message.chat.id, text, kb)
    await callback.answer()

@dp.message(PanelStates.cns_new_screen_key)
async def process_cns_new_screen_key(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    scr_key = message.text.strip().lower().replace(" ", "_")
    try:
        await message.delete()
    except Exception:
        pass

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT screen_key FROM bot_screens WHERE screen_key = ?", (scr_key,))
        if c.fetchone():
            scr_key = f"{scr_key}_{uuid.uuid4().hex[:4]}"

    await state.update_data(cns_scr_key=scr_key)
    await state.set_state(PanelStates.cns_new_screen_title)

    text = (
        f"{PE_EDIT} <b>СОЗДАНИЕ НОВОГО ЭКРАНА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ID Экрана:</b> <code>{scr_key}</code>\n\n"
        f"<b>Шаг 2 из 3:</b> Введите название экрана для панели админа (например: <code>📌 Правила сервиса</code>):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cns_main", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(message.chat.id, text, kb)

@dp.message(PanelStates.cns_new_screen_title)
async def process_cns_new_screen_title(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    scr_title = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(cns_scr_title=scr_title)
    await state.set_state(PanelStates.cns_new_screen_text)

    data = await state.get_data()
    scr_key = data.get("cns_scr_key")

    text = (
        f"{PE_FILE} <b>СОЗДАНИЕ НОВОГО ЭКРАНА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ID Экрана:</b> <code>{scr_key}</code>\n"
        f"<b>Название:</b> <b>{scr_title}</b>\n\n"
        f"<b>Шаг 3 из 3:</b> Отправьте текст сообщения для этого экрана (поддерживается HTML форматирование):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cns_main", icon_custom_emoji_id=ID_CROSS)]
    ])
    await render_panel(message.chat.id, text, kb)

@dp.message(PanelStates.cns_new_screen_text)
async def process_cns_new_screen_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    scr_text = message.text or message.caption or ""
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    scr_key = data.get("cns_scr_key")
    scr_title = data.get("cns_scr_title", "Новый экран")
    now_str = format_now()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO bot_screens (screen_key, title, message_text, is_system, updated_at)
            VALUES (?, ?, ?, 0, ?)
        """, (scr_key, scr_title, scr_text, now_str))
        conn.execute("""
            INSERT INTO bot_buttons (screen_key, btn_text, icon_emoji_id, action_type, action_value, row_index, col_index, is_active, sort_order)
            VALUES (?, 'Главное меню', ?, 'callback', 'to_main_menu', 0, 0, 1, 0)
        """, (scr_key, ID_BACK))
        conn.commit()

    await state.clear()
    await render_screen_editor(message.chat.id, scr_key)

@dp.callback_query(F.data.startswith("cns_del_scr:"))
async def cb_cns_del_screen(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    screen_key = callback.data.split("cns_del_scr:", 1)[1]
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT is_system FROM bot_screens WHERE screen_key = ?", (screen_key,))
        row = c.fetchone()
        if row and row["is_system"]:
            await callback.answer("Системный экран нельзя удалить! Вы можете сбросить его или настроить кнопки.", show_alert=True)
            return
        conn.execute("DELETE FROM bot_screens WHERE screen_key = ?", (screen_key,))
        conn.execute("DELETE FROM bot_buttons WHERE screen_key = ?", (screen_key,))
        conn.commit()

    await callback.answer("Экран и его кнопки успешно удалены!", show_alert=True)
    await render_constructor_main(callback.message.chat.id)

@dp.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

# =========================================================================
# 15. ТОЧКА ВХОДА (RUNNER)
# =========================================================================
async def ensure_bot_connection():
    global bot
    # 0. Проверяем прямое подключение без прокси (на облачном хостинге работает сразу и надежно)
    try:
        print("[*] Проверка прямого подключения к Telegram API (без прокси)...", flush=True)
        direct_session = make_bot_session(None)
        bot.session = direct_session
        me = await asyncio.wait_for(bot.get_me(), timeout=3.5)
        print(f"[+] Прямое подключение к Telegram API успешно: @{me.username}", flush=True)
        return
    except Exception as e:
        print(f"[*] Прямое подключение недоступно ({e}), проверяем прокси...", flush=True)
        try:
            if bot.session:
                await bot.session.close()
        except Exception:
            pass

    # 1. Проверяем текущее прокси из .env
    if PROXY:
        try:
            bot.session = make_bot_session(PROXY)
            me = await asyncio.wait_for(bot.get_me(), timeout=3.5)
            print(f"[+] Подключение через .env прокси успешно: @{me.username}", flush=True)
            return
        except Exception:
            try:
                if bot.session:
                    await bot.session.close()
            except Exception:
                pass

    # 1. Проверяем резервные файлы
    for fname in ["working_proxy.txt", "found_proxy.txt"]:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    candidate = f.read().strip()
                if candidate:
                    print(f"[*] Проверка резервного прокси ({fname}): {candidate}...", flush=True)
                    bot.session = make_bot_session(candidate)
                    me = await asyncio.wait_for(bot.get_me(), timeout=3.5)
                    print(f"[+] Резервный прокси успешно подключен: @{me.username}", flush=True)
                    # Обновляем .env
                    env_file = os.path.join(BASE_DIR, ".env")
                    with open(env_file, "r", encoding="utf-8") as ef:
                        c = ef.read()
                    import re
                    c = re.sub(r"^PROXY=.*", f"PROXY={candidate}", c, flags=re.MULTILINE)
                    with open(env_file, "w", encoding="utf-8") as ef:
                        ef.write(c)
                    return
            except Exception:
                try:
                    if bot.session:
                        await bot.session.close()
                except Exception:
                    pass

    # 2. Быстрый поиск через свежие источники
    print("[*] Автоматический поиск свежего рабочего прокси...", flush=True)
    try:
        import scan_proxies
        loop = asyncio.get_running_loop()
        proxies = await loop.run_in_executor(None, scan_proxies.get_all)
        sem = asyncio.Semaphore(50)
        found_p = []
        async def _t(p):
            if found_p: return
            async with sem:
                try:
                    from aiohttp_socks import ProxyConnector
                    import aiohttp
                    conn = ProxyConnector.from_url(p)
                    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=2.5)) as sess:
                        async with sess.get(f"https://api.telegram.org/bot{TOKEN}/getMe") as r:
                            if r.status == 200:
                                d = await r.json()
                                if d.get("ok"):
                                    found_p.append(p)
                except Exception:
                    pass
        for i in range(0, min(len(proxies), 900), 150):
            if found_p: break
            await asyncio.gather(*[_t(p) for p in proxies[i:i+150]])
        if found_p:
            new_proxy = found_p[0]
            print(f"[+] Найден свежий рабочий прокси: {new_proxy}", flush=True)
            with open(os.path.join(BASE_DIR, "working_proxy.txt"), "w", encoding="utf-8") as f:
                f.write(new_proxy)
            bot.session = make_bot_session(new_proxy)
            me = await asyncio.wait_for(bot.get_me(), timeout=4.0)
            print(f"[+] Соединение восстановлено: @{me.username}", flush=True)
            return
    except Exception as ex:
        print(f"[!] Ошибка поиска прокси: {ex}", flush=True)

    print("[!] Внимание: не удалось автоматически настроить соединение.", flush=True)

async def main():
    print("=" * 60, flush=True)
    print(f"[+] KeyPulse Telegram Bot запускается на aiogram 3.31...", flush=True)
    print(f"[+] Admin ID: {ADMIN_ID}", flush=True)
    print(f"[+] SQLite DB: {DB_PATH}", flush=True)
    print(f"[+] Премиум эмодзи: Telegram iOS Icons (https://emoji.wivvi.net/)", flush=True)
    print("=" * 60, flush=True)

    # Проверяем и гарантируем связь с серверами Telegram
    await ensure_bot_connection()

    # Очищаем вебхук перед polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("[+] Polling запущен! Бот успешно работает и ожидает сообщений.", flush=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
