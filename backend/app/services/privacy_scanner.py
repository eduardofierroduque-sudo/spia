import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote, quote

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.security import is_internal_url
from app.core.user_config import user_config

logger = logging.getLogger("spia")

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

DATA_BROKERS = [
    "whitepages.com", "spokeo.com", "beenverified.com", "intelius.com",
    "truthfinder.com", "peoplefinders.com", "instantcheckmate.com",
    "mylife.com", "peekyou.com", "thatsthem.com", "fastpeoplesearch.com",
    "usphonebook.com", "nuwber.com", "411.info", "addresses.com",
    "radaris.com", "cyberbackgroundchecks.com", "clustrmaps.com",
    "infotracer.com", "familytreenow.com",
]

SOCIAL_PLATFORMS = {
    "instagram.com": "Instagram", "twitter.com": "X", "x.com": "X",
    "facebook.com": "Facebook", "linkedin.com": "LinkedIn",
    "tiktok.com": "TikTok", "youtube.com": "YouTube", "youtu.be": "YouTube",
    "github.com": "GitHub", "gitlab.com": "GitLab", "reddit.com": "Reddit",
    "twitch.tv": "Twitch", "pinterest.com": "Pinterest",
    "snapchat.com": "Snapchat", "discord.com": "Discord",
    "medium.com": "Medium", "dev.to": "Dev.to", "behance.net": "Behance",
    "dribbble.com": "Dribbble", "tumblr.com": "Tumblr",
    "soundcloud.com": "SoundCloud", "spotify.com": "Spotify",
    "stackoverflow.com": "Stack Overflow", "vimeo.com": "Vimeo",
    "telegram.me": "Telegram", "t.me": "Telegram",
    "threads.net": "Threads", "bsky.app": "Bluesky",
    "onlyfans.com": "OnlyFans", "patreon.com": "Patreon",
    "substack.com": "Substack", "flickr.com": "Flickr",
    "deviantart.com": "DeviantArt", "imgur.com": "Imgur",
    "keybase.io": "Keybase",
}

BREACH_AGGREGATORS = [
    {
        "name": "Have I Been Pwned",
        "url": "https://haveibeenpwned.com/api/v3/breachedaccount/",
        "api_key_header": "hibp-api-key",
        "api_key": "",
        "enabled": False,
    },
    {
        "name": "Firefox Monitor",
        "url": "https://monitor.firefox.com/",
        "enabled": False,
    },
    {
        "name": "Dehashed",
        "url": "https://api.dehashed.com/search",
        "api_key_header": "Authorization",
        "api_key": "",
        "enabled": False,
    },
    {
        "name": "LeakCheck",
        "url": "https://leakcheck.io/api/public",
        "api_key_header": "X-API-Key",
        "api_key": "",
        "enabled": False,
    },
    {
        "name": "Snusbase",
        "url": "https://api.snusbase.com/data/search",
        "api_key_header": "Auth",
        "api_key": "",
        "enabled": False,
    },
    {
        "name": "IntelX",
        "url": "https://2.intelx.io/phonebook/search",
        "api_key_header": "x-key",
        "api_key": "",
        "enabled": False,
    },
]

DARK_WEB_ENGINES = [
    {
        "name": "Ahmia",
        "url": "https://ahmia.fi/search/",
        "type": "clearnet_gateway",
    },
    {
        "name": "Tor66",
        "url": "https://tor66.net/search",
        "type": "onion_gateway",
    },
    {
        "name": "DarkSearch",
        "url": "https://darksearch.io/api/search",
        "type": "clearnet_api",
    },
    {
        "name": "OnionLand",
        "url": "https://onionlandsearchengine.com/search",
        "type": "clearnet_gateway",
    },
]

BREACH_DATABASES = [
    "Collection #1", "Collection #2-5", "Anti Public Combo List",
    "Exploit.in", "BreachCombo", "Cit0day", "LeakedSource",
    "LinkedIn 2021", "Facebook 2019", "Twitter 2020", "Adobe 2013",
    "Dropbox 2012", "MySpace 2013", "Tumblr 2013", "VK 2012",
    "Canva 2019", "Dubsmash 2018", "Zynga 2019", "Zynga 2020",
    "Wattpad 2020", "Apollo 2021", "Clubhouse 2021", "Cognyte 2021",
    "Plex 2022", "Twitter 2023", "Duolingo 2023", "23andMe 2023",
    "AT&T 2024", "National Public Data 2024", "Internet Archive 2024",
]

KNOWN_PASTE_SITES = [
    "pastebin.com", "pastie.org", "ghostbin.com", "hastebin.com",
    "0bin.net", "justpaste.it", "rentry.co", "paste.ee",
    "iv.gg", "throwbin.io", "privatebin.net",
]

KNOWN_LEAK_FORUMS = [
    "cracked.io", "leak.sx", "leaked.to", "sinfulsite.com",
    "breached.to", "xss.is", "exploit.in", "raidforums.com",
    "nulled.to", "cracking.org", "leakbase.io",
]

ALLOWED_SEARCH_HOSTS = {
    "html.duckduckgo.com",
    "api.pwnedpasswords.com",
    "haveibeenpwned.com",
    "api.dehashed.com",
    "leakcheck.io",
    "api.snusbase.com",
    "2.intelx.io",
    "ahmia.fi",
    "tor66.net",
    "darksearch.io",
    "onionlandsearchengine.com",
    "www.instagram.com",
    "www.linkedin.com",
    "github.com",
    "x.com",
    "www.facebook.com",
    "www.youtube.com",
    "www.tiktok.com",
    "www.reddit.com",
    "www.twitch.tv",
    "www.threads.net",
    "medium.com",
    "www.pinterest.com",
    "bsky.app",
}


def _safe_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    if len(url) > 2048:
        return False
    if is_internal_url(url):
        return False
    return True


def detect_query_type(query: str) -> str:
    query = query.strip()
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
        return "email"
    if re.match(r'^\+?[\d\s\-().]{7,20}$', query):
        return "phone"
    if re.match(r'^@?[\w.-]{3,30}$', query) and ' ' not in query:
        return "username"
    return "name"


class SecurePrivacyScanner:
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(6.0, connect=5.0),
                follow_redirects=True,
                headers=SEARCH_HEADERS,
                limits=limits,
                max_redirects=5,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def scan(self, query: str, query_type: str = "auto") -> dict:
        if query_type == "auto":
            query_type = detect_query_type(query)
        query = query.strip().lstrip('@')

        try:
            return await asyncio.wait_for(
                self._do_scan(query, query_type),
                timeout=90.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Scan timeout for query type=%s", query_type)
            return {
                "exposures": [],
                "categories": {},
                "data_sources": [],
                "privacy_score": 100,
                "recommendations": [
                    "The scan exceeded the time limit. DuckDuckGo may be rate-limited.",
                    "Please retry in 2-3 minutes.",
                    "For faster results, configure API keys in Settings.",
                ],
                "total_exposures": 0,
            }

    async def _do_scan(self, query: str, query_type: str) -> dict:
        results: list[dict] = []

        async def safe_collect(coro):
            try:
                r = await coro
                if isinstance(r, list):
                    results.extend(r)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Scan sub-task failed: %s", str(exc)[:100])

        tasks = []

        if query_type == "email":
            tasks.extend([
                safe_collect(self._search_email_exposure(query)),
                safe_collect(self._search_email_on_social(query)),
                safe_collect(self._check_hibp_api(query)),
                safe_collect(self._search_breach_databases(query)),
                safe_collect(self._search_paste_sites(query)),
                safe_collect(self._search_dark_web(query)),
                safe_collect(self._search_leak_forums(query)),
                safe_collect(self._check_dehashed_api(query)),
            ])

        if query_type == "name":
            tasks.append(safe_collect(self._search_name_direct(query)))
        else:
            tasks.extend([
                safe_collect(self._search_username_platforms(query)),
                safe_collect(self._search_public_records(query)),
            ])

        if query_type == "phone":
            tasks.append(safe_collect(self._search_phone_exposure(query)))

        tasks.append(safe_collect(self._search_images(query)))

        await asyncio.gather(*tasks)

        categories = self._build_categories(results)
        data_sources = list(dict.fromkeys(r["label"] for r in results))
        privacy_score = self._compute_privacy_score(results, query_type)
        recommendations = self._generate_recommendations(results, query_type)

        images = [r for r in results if r.get("category") == "image"]
        exposures = [r for r in results if r.get("category") != "image"]

        return {
            "exposures": exposures,
            "images": images,
            "categories": categories,
            "data_sources": data_sources,
            "privacy_score": privacy_score,
            "recommendations": recommendations,
            "total_exposures": len(exposures),
        }

    async def _search_ddg(self, query: str) -> list[str]:
        urls = []
        try:
            client = await self._get_client()
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query, "kl": "us-en"},
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.select("a.result__a"):
                    href = link.get("href", "")
                    if "uddg=" in href:
                        decoded = unquote(href.split("uddg=")[1].split("&")[0])
                        if decoded.startswith("http") and _safe_url(decoded):
                            urls.append(decoded)
                    elif href.startswith("http") and _safe_url(href):
                        urls.append(href)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("DuckDuckGo search failed: %s", str(exc)[:100])
        return urls[:15]

    async def _search_web(self, query: str) -> list[str]:
        cfg = user_config.get_config()

        if cfg.serpapi_key:
            urls = await self._search_serpapi(query, cfg.serpapi_key)
            if urls:
                return urls

        if cfg.google_api_key and cfg.google_cse_id:
            urls = await self._search_google_cse(query, cfg.google_api_key, cfg.google_cse_id)
            if urls:
                return urls

        return await self._search_web(query)

    async def _search_serpapi(self, query: str, api_key: str) -> list[str]:
        urls = []
        try:
            client = await self._get_client()
            response = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "engine": "google", "num": 15},
            )
            if response.status_code == 200:
                data = response.json()
                for result in data.get("organic_results", []):
                    link = result.get("link", "")
                    if link and _safe_url(link):
                        urls.append(link)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("SerpAPI search failed: %s", str(exc)[:100])
        return urls[:15]

    async def _search_google_cse(self, query: str, api_key: str, cse_id: str) -> list[str]:
        urls = []
        try:
            client = await self._get_client()
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"q": query, "key": api_key, "cx": cse_id, "num": 10},
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    link = item.get("link", "")
                    if link and _safe_url(link):
                        urls.append(link)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Google CSE search failed: %s", str(exc)[:100])
        return urls[:15]

    async def _check_hibp_api(self, email: str) -> list[dict]:
        results = []
        try:
            client = await self._get_client()
            sha1_email = hashlib.sha1(email.encode()).hexdigest().upper()
            prefix, suffix = sha1_email[:5], sha1_email[5:]

            response = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "SPIA-Privacy-Auditor"},
            )
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.startswith(suffix):
                        count = int(line.split(":")[1]) if ":" in line else 1
                        results.append({
                            "category": "breach",
                            "label": "Have I Been Pwned",
                            "detail": f"Email found in {count} security breach(es)",
                            "url": f"https://haveibeenpwned.com/account/{email}",
                            "risk_level": "high",
                        })

            settings = get_settings()
            hibp_key = user_config.get_config().hibp_api_key or settings.hibp_api_key
            if hibp_key:
                try:
                    response2 = await client.get(
                        f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}",
                        headers={
                            "User-Agent": "SPIA-Privacy-Auditor",
                            "hibp-api-key": hibp_key,
                            "Accept": "application/json",
                        },
                    )
                    if response2.status_code == 200:
                        breaches = response2.json()
                        for breach in breaches[:15]:
                            name = breach.get("Name", "Unknown")
                            domain = breach.get("Domain", "unknown")
                            desc = breach.get("Description", "")
                            date = breach.get("BreachDate", "")
                            results.append({
                                "category": "breach",
                                "label": name,
                                "detail": f"{desc[:100]} — {date}" if desc else f"Breach on {domain} — {date}",
                                "url": f"https://haveibeenpwned.com/account/{email}",
                                "risk_level": "high",
                            })
                except Exception as exc:
                    logger.debug("HIBP v3 API failed: %s", str(exc)[:100])
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("HIBP check failed: %s", str(exc)[:100])
        return results[:15]

    async def _search_breach_databases(self, email: str) -> list[dict]:
        results = []
        queries = [
            f'"{email}" breach OR leak OR pwned OR database OR dump',
            f'"{email}" site:cracked.io OR site:leaked.to OR site:exploit.in',
            f'"{email}" site:pastebin.com OR site:justpaste.it OR site:rentry.co',
        ]

        seen = set()
        for q in queries[:2]:
            urls = await self._search_web(q)
            for url in urls:
                domain = urlparse(url).netloc.lower().lstrip("www.")
                if domain in seen:
                    continue
                seen.add(domain)

                is_paste = any(p in domain for p in KNOWN_PASTE_SITES)
                is_forum = any(f in domain for f in KNOWN_LEAK_FORUMS)

                cat = "leak" if is_paste else "exposure"
                risk = "high" if (is_paste or is_forum) else "medium"

                results.append({
                    "category": cat,
                    "label": domain[:40],
                        "detail": "Possible exposure in leaked database",
                    "url": url,
                    "risk_level": risk,
                })

        return results[:10]

    async def _search_paste_sites(self, query: str) -> list[dict]:
        results = []
        for site in KNOWN_PASTE_SITES[:5]:
            urls = await self._search_web(f'"{query}" site:{site}')
            for url in urls:
                results.append({
                    "category": "leak",
                    "label": site,
                        "detail": "Data found on public paste site",
                    "url": url,
                    "risk_level": "high",
                })
            await asyncio.sleep(0.15)
        return results[:8]

    async def _search_leak_forums(self, query: str) -> list[dict]:
        results = []
        seen = set()
        for forum in KNOWN_LEAK_FORUMS[:5]:
            urls = await self._search_web(f'"{query}" site:{forum}')
            for url in urls:
                domain = urlparse(url).netloc.lower().lstrip("www.")
                if domain in seen:
                    continue
                seen.add(domain)
                results.append({
                    "category": "leak",
                    "label": domain,
                        "detail": "Mention in leak forum",
                    "url": url,
                    "risk_level": "high",
                })
            await asyncio.sleep(0.15)
        return results[:5]

    async def _search_dark_web(self, query: str) -> list[dict]:
        results = []
        for engine in DARK_WEB_ENGINES[:2]:
            try:
                client = await self._get_client()
                if engine["type"] == "clearnet_gateway":
                    response = await client.get(
                        engine["url"],
                        params={"q": f'"{query}"'},
                    )
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        links = 0
                        for a in soup.select("a[href]"):
                            href = a.get("href", "")
                            if href.startswith("http") and "ahmia" not in href and "tor66" not in href:
                                results.append({
                                    "category": "darkweb",
                                    "label": engine["name"],
                                        "detail": f"Dark web result via {engine['name']}",
                                    "url": href,
                                    "risk_level": "high",
                                })
                                links += 1
                                if links >= 3:
                                    break
                elif engine["type"] == "clearnet_api":
                    response = await client.get(
                        engine["url"],
                        params={"query": query},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("data", [])[:5]:
                            results.append({
                                "category": "darkweb",
                                "label": engine["name"],
                                        "detail": item.get("title", "Dark web result")[:100],
                                "url": item.get("link", ""),
                                "risk_level": "high",
                            })
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Dark web search %s failed: %s", engine["name"], str(exc)[:100])
            await asyncio.sleep(0.2)
        return results[:8]

    async def _check_dehashed_api(self, email: str) -> list[dict]:
        results = []
        cfg = user_config.get_config()
        if not cfg.dehashed_api_key or not cfg.dehashed_email:
            return results

        try:
            client = await self._get_client()
            response = await client.get(
                "https://api.dehashed.com/search",
                params={"query": email},
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Basic {__import__('base64').b64encode(f'{cfg.dehashed_email}:{cfg.dehashed_api_key}'.encode()).decode()}",
                    "User-Agent": "SPIA-Privacy-Auditor",
                },
            )
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                for entry in entries[:20]:
                    db = entry.get("database_name", "Desconocida")
                    detail_parts = []
                    if entry.get("email"):
                        detail_parts.append(f"Email: {entry['email']}")
                    if entry.get("password"):
                        detail_parts.append("Password: ***")
                    if entry.get("username"):
                        detail_parts.append(f"User: {entry['username']}")
                    results.append({
                        "category": "breach",
                        "label": db,
                        "detail": " | ".join(detail_parts) if detail_parts else f"Record in {db}",
                        "url": f"https://dehashed.com/search?query={quote(email)}",
                        "risk_level": "high",
                    })
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Dehashed API failed: %s", str(exc)[:100])
        return results

    async def _search_username_platforms(self, username: str) -> list[dict]:
        results = []
        seen = set()

        batch_queries = [
            f'"{username}" site:instagram.com OR site:twitter.com OR site:x.com OR site:facebook.com OR site:tiktok.com OR site:linkedin.com OR site:github.com',
            f'"{username}" site:youtube.com OR site:reddit.com OR site:medium.com OR site:twitch.tv OR site:threads.net OR site:itch.io OR site:stackoverflow.com',
        ]

        for q in batch_queries:
            urls = await self._search_web(q)
            for url in urls:
                domain = urlparse(url).netloc.lower().lstrip("www.")
                label = None
                for known, l in SOCIAL_PLATFORMS.items():
                    if known in domain:
                        label = l
                        break
                if label is None or label in seen:
                    continue
                seen.add(label)
                path = urlparse(url).path.strip("/")
                skip = {"u", "user", "in", "p", "watch", "reel", "posts", "status", "spaces", "embed"}
                parts = [p for p in path.split("/") if p and p not in skip]
                handle = username
                for p in parts:
                    if username.lower() in p.lower():
                        handle = p
                        break
                results.append({
                    "category": "social",
                    "label": label,
                    "detail": handle,
                    "url": url,
                    "risk_level": "low",
                })
            await asyncio.sleep(0.1)
        return results

    async def _search_email_exposure(self, email: str) -> list[dict]:
        results = []
        all_urls = set(await self._search_web(f'"{email}"'))
        for url in all_urls:
            domain = urlparse(url).netloc.lower().lstrip("www.")
            is_leak = any(p in domain for p in KNOWN_PASTE_SITES)
            is_forum = any(f in domain for f in KNOWN_LEAK_FORUMS)
            is_broker = any(b in domain for b in DATA_BROKERS)
            cat = "leak" if (is_leak or is_forum) else "databroker" if is_broker else "exposure"
            risk = "high" if (is_leak or is_forum) else "medium" if is_broker else "low"
            detail = "Email exposed in leak/paste" if is_leak else \
                     "Email in leak forum" if is_forum else \
                     "Email in data broker" if is_broker else \
                     "Email publicly exposed"
            results.append({
                "category": cat, "label": domain[:40], "detail": detail,
                "url": url, "risk_level": risk,
            })
        return results[:15]

    async def _search_email_on_social(self, email: str) -> list[dict]:
        results = []
        seen = set()
        local = email.split("@")[0]
        for q in [f'"{email}" site:linkedin.com OR site:github.com', f'"{local}" site:twitter.com OR site:x.com']:
            for url in await self._search_web(q):
                domain = urlparse(url).netloc.lower().lstrip("www.")
                label = SOCIAL_PLATFORMS.get(domain, domain)
                if label in seen:
                    continue
                seen.add(label)
                results.append({
                    "category": "social", "label": label,
                    "detail": f"Email associated with {label}", "url": url, "risk_level": "low",
                })
        return results[:5]

    async def _search_public_records(self, query: str) -> list[dict]:
        results = []
        seen = set()
        for broker in DATA_BROKERS[:6]:
            urls = await self._search_web(f'"{query}" site:{broker}')
            for url in urls:
                domain = urlparse(url).netloc.lower().lstrip("www.")
                if domain in seen:
                    continue
                seen.add(domain)
                results.append({
                    "category": "databroker", "label": broker.split(".")[0].title(),
                    "detail": f"Possible public record on {broker}",
                    "url": url, "risk_level": "medium",
                })
                if len(results) >= 6:
                    break
            if len(results) >= 6:
                break
            await asyncio.sleep(0.1)
        return results[:6]

    async def _search_name_direct(self, name: str) -> list[dict]:
        results = []
        seen = set()
        client = await self._get_client()

        name_slug = name.lower().replace(" ", "-")
        name_parts = name.lower().split()
        first = name_parts[0] if name_parts else name.lower()
        last = name_parts[-1] if len(name_parts) > 1 else ""

        profile_checks = [
            ("LinkedIn", f"https://www.linkedin.com/in/{name_slug}/"),
            ("LinkedIn", f"https://www.linkedin.com/in/{first}-{last}/"),
            ("GitHub", f"https://github.com/{name_slug}"),
            ("GitHub", f"https://github.com/{first}{last}"),
            ("Twitter/X", f"https://x.com/{name_slug}"),
            ("Twitter/X", f"https://x.com/{first}{last}"),
            ("Instagram", f"https://www.instagram.com/{first}{last}/"),
            ("Instagram", f"https://www.instagram.com/{name_slug}/"),
            ("Facebook", f"https://www.facebook.com/{name_slug}"),
            ("Facebook", f"https://www.facebook.com/{first}.{last}"),
            ("YouTube", f"https://www.youtube.com/@{name_slug}"),
            ("YouTube", f"https://www.youtube.com/@{first}{last}"),
            ("TikTok", f"https://www.tiktok.com/@{first}{last}"),
            ("Reddit", f"https://www.reddit.com/user/{name_slug}"),
            ("Twitch", f"https://www.twitch.tv/{name_slug}"),
            ("Threads", f"https://www.threads.net/@{first}{last}"),
            ("Medium", f"https://medium.com/@{name_slug}"),
            ("Pinterest", f"https://www.pinterest.com/{name_slug}/"),
            ("Bluesky", f"https://bsky.app/profile/{name_slug}.bsky.social"),
        ]

        tasks = []
        for label, url in profile_checks:
            tasks.append(self._check_profile_url(client, label, url, name, seen))

        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.append(result)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Profile check failed: %s", str(exc)[:100])

        web_results = await self._search_personal_website(client, name, first, last, seen)
        results.extend(web_results)

        return results

    async def _check_profile_url(self, client, label: str, url: str, name: str, seen: set) -> dict | None:
        if label in seen:
            return None
        if not _safe_url(url):
            return None
        try:
            response = await client.get(url, follow_redirects=True,
                                         timeout=httpx.Timeout(4.0, connect=3.0))
            final_url = str(response.url)
            if response.status_code == 200 and "login" not in final_url.lower():
                seen.add(label)
                return {
                    "category": "social",
                    "label": label,
                    "detail": f"Profile of {name} on {label}",
                    "url": final_url if final_url != url else url,
                    "risk_level": "low",
                }
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Profile URL check %s failed: %s", url[:60], str(exc)[:100])
        return None

    async def _search_personal_website(self, client, name: str, first: str, last: str, seen: set) -> list[dict]:
        results = []
        name_slug = name.replace(" ", "")

        domain_checks = [
            f"https://www.{first}{last}.com",
            f"https://{first}{last}.com",
            f"https://www.{first}{last}.es",
            f"https://{first}{last}.es",
            f"https://www.{first}{last}.me",
            f"https://{first}{last}.me",
            f"https://www.{first}{last}.io",
            f"https://{first}{last}.io",
            f"https://www.{name_slug}.com",
            f"https://{name_slug}.com",
            f"https://www.{name.replace(' ', '')}.com",
        ]

        for url in domain_checks:
            if not _safe_url(url):
                continue
            try:
                response = await client.get(url, follow_redirects=True,
                                             timeout=httpx.Timeout(4.0, connect=3.0))
                final_url = str(response.url)
                if response.status_code == 200 and len(response.text) > 500:
                    results.append({
                        "category": "web",
                        "label": "Sitio Personal",
                        "detail": f"Personal website of {name}",
                        "url": final_url if final_url != url else url,
                        "risk_level": "low",
                    })
                    break
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Personal website check failed: %s", str(exc)[:100])

        return results

    async def _search_phone_exposure(self, phone: str) -> list[dict]:
        results = []
        clean = re.sub(r'[\s\-()]', '', phone)
        for q in [f'"{phone}"', f'"{clean}"']:
            for url in await self._search_web(q):
                domain = urlparse(url).netloc.lower().lstrip("www.")
                is_broker = any(b in domain for b in DATA_BROKERS)
                results.append({
                    "category": "databroker" if is_broker else "exposure",
                    "label": domain[:40],
                    "detail": "Phone in data broker" if is_broker else "Phone exposed",
                    "url": url, "risk_level": "high" if is_broker else "medium",
                })
        return results[:10]

    async def _search_images(self, query: str) -> list[dict]:
        results = []
        try:
            client = await self._get_client()

            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query, "t": "h_", "iax": "images", "ia": "images"},
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a"):
                    href = link.get("href", "")
                    if "uddg=" not in href:
                        continue
                    decoded = unquote(href.split("uddg=")[1].split("&")[0])
                    if not decoded.startswith("http") or not _safe_url(decoded):
                        continue
                    domain = urlparse(decoded).netloc.lower().lstrip("www.")

                    img_tag = link.find("img")
                    thumb_src = ""
                    if img_tag:
                        thumb_src = img_tag.get("src", "")
                        if thumb_src and thumb_src.startswith("//"):
                            thumb_src = "https:" + thumb_src

                    image_url = thumb_src if thumb_src and thumb_src.startswith("http") and _safe_url(thumb_src) else decoded

                    results.append({
                        "category": "image",
                        "label": domain[:35] or "web",
                        "detail": f"Image on {domain[:35]}",
                        "url": image_url,
                        "risk_level": "low",
                    })
                    if len(results) >= 20:
                        break

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Image search failed: %s", str(exc)[:100])

        return results[:20]

    def _build_categories(self, results: list[dict]) -> dict[str, int]:
        cats: dict[str, int] = {}
        for r in results:
            cat = r.get("category", "other")
            cats[cat] = cats.get(cat, 0) + 1
        return cats

    def _compute_privacy_score(self, results: list[dict], query_type: str) -> int:
        if not results:
            return 100
        high = sum(1 for r in results if r.get("risk_level") == "high")
        medium = sum(1 for r in results if r.get("risk_level") == "medium")
        darkweb = sum(1 for r in results if r.get("category") == "darkweb")
        leaks = sum(1 for r in results if r.get("category") in ("breach", "leak"))
        score = 100 - high * 10 - medium * 4 - darkweb * 8 - leaks * 6 - len(results) * 0.3
        return max(0, min(100, int(score)))

    def _generate_recommendations(self, results: list[dict], query_type: str) -> list[str]:
        recs = []
        cats = self._build_categories(results)
        if cats.get("breach", 0) > 0:
            recs.append("Change your passwords immediately. Use a password manager (Bitwarden, 1Password).")
            recs.append("Enable 2FA on all accounts where your email appears compromised.")
        if cats.get("leak", 0) > 0 or cats.get("darkweb", 0) > 0:
            recs.append("Your data is circulating on the dark web. Monitor for suspicious activity.")
            recs.append("Consider freezing your credit if financial data is exposed.")
        if cats.get("databroker", 0) > 0:
            recs.append(f"You have profiles on {cats['databroker']} data brokers. Request opt-out removal on each one.")
            recs.append("Use services like DeleteMe, Optery or Kanary to automatically remove your data.")
        if cats.get("social", 0) > 0:
            recs.append(f"You appear on {cats['social']} social networks. Review the privacy settings of each one.")
        if query_type == "email" and not cats.get("breach", 0) and not cats.get("leak", 0):
            recs.append("Your email does not appear in known breaches. Keep up good security practices.")
        if not results:
            recs.append("No exposures detected. Your digital footprint is low.")
            recs.append("Stay alert: periodically check your email on haveibeenpwned.com.")
        return recs[:6]


privacy_scanner = SecurePrivacyScanner()
