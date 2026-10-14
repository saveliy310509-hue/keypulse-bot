import asyncio
import urllib.request
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
TOKEN = os.getenv("TOKENBOT", "")
TEST_URL = f"https://api.telegram.org/bot{TOKEN}/getMe"

urls = [
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt"
]

def get_all():
    proxies = []
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            txt = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")
            proto = "socks5" if "socks5" in u else "http"
            for l in txt.splitlines():
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                if "://" not in l:
                    proxies.append(f"{proto}://{l}")
                else:
                    proxies.append(l)
        except Exception:
            pass
    return list(dict.fromkeys(proxies))

found = []

async def test_one(p, sem):
    if len(found) >= 3:
        return
    async with sem:
        try:
            if p.startswith("socks"):
                conn = ProxyConnector.from_url(p)
                async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=3.5)) as session:
                    async with session.get(TEST_URL) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data.get("ok"):
                                print(f"[+] НАЙДЕН РАБОЧИЙ ПРОКСИ: {p} (Bot: @{data['result']['username']})")
                                found.append(p)
            else:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3.5)) as session:
                    async with session.get(TEST_URL, proxy=p) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data.get("ok"):
                                print(f"[+] НАЙДЕН РАБОЧИЙ ПРОКСИ: {p} (Bot: @{data['result']['username']})")
                                found.append(p)
        except Exception:
            pass

async def main():
    proxies = get_all()
    print(f"Всего уникальных прокси для проверки: {len(proxies)}")
    sem = asyncio.Semaphore(75)
    
    # Проверяем пачками по 300
    for i in range(0, len(proxies), 300):
        if len(found) >= 3:
            break
        batch = proxies[i:i+300]
        print(f"Проверка пачки {i}..{i+len(batch)}...")
        await asyncio.gather(*[test_one(p, sem) for p in batch])
    
    print("\nИТОГО РАБОЧИХ:")
    for f in found:
        print(" ->", f)

    if found:
        with open("working_proxy.txt", "w") as fp:
            fp.write(found[0])

if __name__ == "__main__":
    asyncio.run(main())
