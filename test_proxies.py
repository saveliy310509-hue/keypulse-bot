import asyncio
import aiohttp
import urllib.request
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
TOKEN = os.getenv("TOKENBOT", "")
TEST_URL = f"https://api.telegram.org/bot{TOKEN}/getMe"

SOURCES = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=4000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=4000&country=all"
]

def load_proxies():
    proxies = set()
    for s in SOURCES:
        try:
            req = urllib.request.Request(s, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=4).read().decode("utf-8", errors="ignore")
            for line in data.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "://" in line:
                    proxies.add(line)
                else:
                    if "socks5" in s:
                        proxies.add(f"socks5://{line}")
                    else:
                        proxies.add(f"http://{line}")
        except Exception:
            pass
    print(f"[+] Собрано {len(proxies)} прокси для проверки.")
    return list(proxies)

async def check_proxy(proxy: str, working_list: list, sem: asyncio.Semaphore):
    async with sem:
        try:
            if proxy.startswith("socks"):
                connector = ProxyConnector.from_url(proxy)
                async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=4)) as session:
                    async with session.get(TEST_URL) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("ok"):
                                bot_user = data["result"]["username"]
                                print(f"[✓ РАБОТАЕТ!] {proxy} -> @{bot_user}")
                                working_list.append(proxy)
            else:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
                    async with session.get(TEST_URL, proxy=proxy) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("ok"):
                                bot_user = data["result"]["username"]
                                print(f"[✓ РАБОТАЕТ!] {proxy} -> @{bot_user}")
                                working_list.append(proxy)
        except Exception:
            pass

async def main():
    all_proxies = load_proxies()
    # Возьмем первые 300 для быстрой проверки
    to_check = all_proxies[:300]
    sem = asyncio.Semaphore(50)
    working = []
    
    tasks = [asyncio.create_task(check_proxy(p, working, sem)) for p in to_check]
    
    # Ждем первых нескольких работающих
    done, pending = await asyncio.wait(tasks, timeout=12)
    for t in pending:
        t.cancel()

    print(f"\n[+] Найдено рабочих прокси: {len(working)}")
    if working:
        print("Список первых рабочих:")
        for w in working[:5]:
            print("  ", w)
        with open("working_proxy.txt", "w", encoding="utf-8") as f:
            f.write(working[0])

if __name__ == "__main__":
    asyncio.run(main())
