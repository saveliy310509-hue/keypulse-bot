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
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
    "https://raw.githubusercontent.com/tuanminpay/live-proxy/master/socks5.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt"
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
                    if "socks5" in s:
                        proxies.add(f"socks5://{line}")
                    else:
                        proxies.add(f"http://{line}")
                else:
                    proxies.add(line)
        except Exception:
            pass
    return list(proxies)

async def find_one_working_proxy(token: str = TOKEN) -> str:
    test_url = f"https://api.telegram.org/bot{token}/getMe"
    loop = asyncio.get_running_loop()
    proxies = await loop.run_in_executor(None, fetch)
    if not proxies:
        return ""
    
    found_proxies = []
    sem = asyncio.Semaphore(100)

    async def _test(p):
        if found_proxies:
            return
        async with sem:
            try:
                if p.startswith("socks"):
                    conn = ProxyConnector.from_url(p)
                    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=2.5)) as session:
                        async with session.get(test_url) as resp:
                            if resp.status == 200:
                                d = await resp.json()
                                if d.get("ok"):
                                    found_proxies.append(p)
                else:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.5)) as session:
                        async with session.get(test_url, proxy=p) as resp:
                            if resp.status == 200:
                                d = await resp.json()
                                if d.get("ok"):
                                    found_proxies.append(p)
            except Exception:
                pass

    for i in range(0, len(proxies), 150):
        if found_proxies:
            break
        chunk = proxies[i:i+150]
        await asyncio.gather(*[_test(p) for p in chunk])
        if found_proxies:
            break

    return found_proxies[0] if found_proxies else ""

async def main():
    print("Ищем рабочий прокси...", flush=True)
    p = await find_one_working_proxy(TOKEN)
    if p:
        print(f"\n[!!! НАЙДЕН РАБОЧИЙ ПРОКСИ !!!] -> {p}", flush=True)
        with open("found_proxy.txt", "w") as f:
            f.write(p)
    else:
        print("Не удалось найти рабочий прокси.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

