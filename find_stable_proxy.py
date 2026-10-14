import asyncio
import urllib.request
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
TOKEN = os.getenv("TOKENBOT", "")
TEST_URL = f"https://api.telegram.org/bot{TOKEN}/getMe"

SOURCES = [
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/socks5.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
]

def fetch():
    proxies = set()
    for s in SOURCES:
        try:
            req = urllib.request.Request(s, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=4).read().decode("utf-8", errors="ignore")
            for line in data.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "://" not in line:
                    proxies.add(f"socks5://{line}")
                else:
                    proxies.add(line)
        except Exception:
            pass
    return list(proxies)

stable_proxies = []

async def test_proxy(proxy, sem):
    if len(stable_proxies) >= 3:
        return
    async with sem:
        try:
            conn = ProxyConnector.from_url(proxy)
            # Тестируем 2 запроса подряд для проверки стабильности
            async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=4)) as session:
                async with session.get(TEST_URL) as r1:
                    if r1.status != 200:
                        return
                    d1 = await r1.json()
                    if not d1.get("ok"):
                        return
                
                # Второй проверочный запрос (getMe еще раз)
                async with session.get(TEST_URL) as r2:
                    if r2.status == 200:
                        d2 = await r2.json()
                        if d2.get("ok"):
                            print(f"[✓ СТАБИЛЕН!] {proxy} (2/2 успешно!)", flush=True)
                            stable_proxies.append(proxy)
        except Exception:
            pass

async def main():
    proxies = fetch()
    print(f"[+] Собрано {len(proxies)} SOCKS5 прокси. Проверка стабильности...", flush=True)
    sem = asyncio.Semaphore(100)
    
    for i in range(0, len(proxies), 150):
        if len(stable_proxies) >= 3:
            break
        chunk = proxies[i:i+150]
        await asyncio.gather(*[test_proxy(p, sem) for p in chunk])

    print(f"\n[+] ИТОГО НАЙДЕНО СТАБИЛЬНЫХ: {len(stable_proxies)}", flush=True)
    for p in stable_proxies:
        print("  ->", p)
        
    if stable_proxies:
        with open("working_proxy.txt", "w") as f:
            f.write(stable_proxies[0])

if __name__ == "__main__":
    asyncio.run(main())
