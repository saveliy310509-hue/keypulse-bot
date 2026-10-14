import hashlib
import platform
import subprocess
import sys
import time
import requests

SERVER_URL = "http://127.0.0.1:8000"

def get_hwid() -> str:
    """
    Генерирует уникальный аппаратный отпечаток (HWID) компьютера.
    В Windows использует UUID системы или процессор + материнскую плату.
    """
    hwid_raw = ""
    try:
        # Для Windows получаем UUID компьютера через wmic / powershell
        cmd = 'powershell -command "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"'
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
        if output:
            hwid_raw = output
    except Exception:
        pass

    if not hwid_raw:
        # Резервный кроссплатформенный вариант
        hwid_raw = f"{platform.node()}-{platform.processor()}-{platform.machine()}"

    # Хэшируем в надежный 24-значный идентификатор
    return f"HWID-{hashlib.sha256(hwid_raw.encode()).hexdigest()[:20].upper()}"

def main():
    print("=" * 60)
    print("   🛡️ ДЕМО-ПРИЛОЖЕНИЕ: СИСТЕМА ЛИЦЕНЗИРОВАНИЯ И ЗАЩИТЫ")
    print("=" * 60)

    hwid = get_hwid()
    print(f"\n[+] Идентификатор вашего ПК (HWID): {hwid}")
    print("[*] Подключение к серверу проверки лицензий...")

    is_admin = "--admin" in sys.argv
    if is_admin:
        print("\n👑 [ВНИМАНИЕ]: Запущен в РЕЖИМЕ АДМИНИСТРАТОРА (Обход HWID и ограничений включен)!")

    # 1. Проверяем, есть ли уже привязанная лицензия для этого устройства
    try:
        res = requests.post(
            f"{SERVER_URL}/api/client/verify", 
            json={"hwid": hwid, "admin_mode": is_admin}, 
            timeout=5
        )
        data = res.json()
        
        if res.status_code == 200 and data.get("valid"):
            print(f"\n[✅] ЛИЦЕНЗИЯ АКТИВНА!")
            print(f"     Ключ: {data.get('key')}")
            print(f"     Бессрочная: {'Да' if data.get('is_lifetime') else 'До ' + str(data.get('expires_at'))}")
            run_main_program()
            return
    except requests.exceptions.ConnectionError:
        print("\n[❌] ОШИБКА: Сервер лицензий недоступен!")
        print(f"     Убедитесь, что сервер запущен по адресу: {SERVER_URL}")
        input("\nНажмите Enter для выхода...")
        return
    except Exception as e:
        print(f"\n[❌] Неизвестная ошибка: {e}")
        return

    # 2. Если устройство еще не активировано — просим ключ
    print("\n[!] Ваше устройство еще не активировано.")
    key = input("👉 Введите ключ доступа (например, PRO-XXXX-XXXX-XXXX): ").strip()

    if not key:
        print("[-] Ключ не введен. Завершение работы.")
        return

    print("\n[*] Проверка ключа на сервере...")
    try:
        act_res = requests.post(
            f"{SERVER_URL}/api/client/activate",
            json={"key": key, "hwid": hwid, "admin_mode": is_admin},
            timeout=5
        )
        act_data = act_res.json()

        if act_res.status_code == 200 and act_data.get("success"):
            print("\n" + "=" * 60)
            print("[🎉] УСПЕШНАЯ АКТИВАЦИЯ!")
            print(f"     {act_data.get('message')}")
            print(f"     Ключ привязан к HWID: {hwid}")
            print("=" * 60)
            run_main_program()
        else:
            error_detail = act_data.get("detail", "Ошибка активации")
            print("\n" + "=" * 60)
            print(f"[⛔] ДОСТУП ЗАПРЕЩЕН: {error_detail}")
            print("=" * 60)
            input("\nНажмите Enter для выхода...")
    except Exception as e:
        print(f"\n[❌] Ошибка запроса: {e}")

def run_main_program():
    """Запуск защищенной логики приложения"""
    print("\n" + "-" * 50)
    print("🚀 [СЕКРЕТНЫЙ ФУНКЦИОНАЛ ПРИЛОЖЕНИЯ ЗАПУЩЕН]")
    print("    Добро пожаловать в премиум-модуль!")
    print("    Все функции программы разблокированы.")
    print("-" * 50)
    input("\nНажмите Enter для завершения программы...")

if __name__ == "__main__":
    main()
