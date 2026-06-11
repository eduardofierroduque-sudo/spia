import asyncio
import logging
import re
from urllib.parse import urlparse, unquote

import httpx
from bs4 import BeautifulSoup

from app.core.security import is_internal_url

logger = logging.getLogger("spia")

KNOWN_PLATFORMS: dict[str, str] = {
    "instagram.com": "Instagram",
    "twitter.com": "X / Twitter",
    "x.com": "X / Twitter",
    "tiktok.com": "TikTok",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "itch.io": "itch.io",
    "twitch.tv": "Twitch",
    "linkedin.com": "LinkedIn",
    "reddit.com": "Reddit",
    "medium.com": "Medium",
    "dev.to": "Dev.to",
    "stackoverflow.com": "Stack Overflow",
    "behance.net": "Behance",
    "dribbble.com": "Dribbble",
    "pinterest.com": "Pinterest",
    "facebook.com": "Facebook",
    "discord.gg": "Discord",
    "discord.com": "Discord",
    "patreon.com": "Patreon",
    "ko-fi.com": "Ko-fi",
    "steamcommunity.com": "Steam",
    "open.spotify.com": "Spotify",
    "soundcloud.com": "SoundCloud",
    "vimeo.com": "Vimeo",
    "linktr.ee": "Linktree",
    "carrd.co": "Carrd",
    "telegram.me": "Telegram",
    "t.me": "Telegram",
    "fiverr.com": "Fiverr",
    "upwork.com": "Upwork",
    "etsy.com": "Etsy",
    "gumroad.com": "Gumroad",
    "substack.com": "Substack",
    "wordpress.com": "WordPress",
    "blogspot.com": "Blogger",
    "tumblr.com": "Tumblr",
    "deviantart.com": "DeviantArt",
    "artstation.com": "ArtStation",
    "imgur.com": "Imgur",
    "flickr.com": "Flickr",
    "threads.net": "Threads",
    "bsky.app": "Bluesky",
    "huggingface.co": "HuggingFace",
    "producthunt.com": "Product Hunt",
}

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}


def _safe_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    if len(url) > 2048:
        return False
    if is_internal_url(url):
        return False
    return True


class WebPresenceSearcher:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=SEARCH_HEADERS,
            max_redirects=5,
        )

    async def search(self, username: str, platform: str = "instagram") -> list[dict]:
        if len(username) > 100:
            return []
        queries = [
            f'"{username}"',
            f'"{username}" profile OR bio OR about OR contact',
            f'"{username}" site:github.com OR site:itch.io OR site:youtube.com',
            f'"{username}" site:linkedin.com OR site:twitter.com OR site:reddit.com',
        ]

        results = await asyncio.gather(
            *[self._search_duckduckgo(q) for q in queries],
            return_exceptions=True,
        )

        all_urls: set[str] = set()
        for r in results:
            if isinstance(r, list):
                all_urls.update(r)

        profiles = self._parse_search_results(list(all_urls), username)
        return profiles

    async def search_posts(self, username: str) -> list[dict]:
        if len(username) > 100:
            return []
        queries = [
            f'"{username}" comment OR replied OR said OR wrote',
            f'"{username}" posted OR shared OR published OR uploaded',
        ]

        results = await asyncio.gather(
            *[self._search_duckduckgo(q) for q in queries],
            return_exceptions=True,
        )

        all_urls: set[str] = set()
        for r in results:
            if isinstance(r, list):
                all_urls.update(r)

        posts = []
        for url in list(all_urls)[:20]:
            domain = urlparse(url).netloc.lower().lstrip("www.")
            snippet = self._extract_snippet_from_url(url, username)

            if self._already_in_known_platforms(domain):
                continue

            title = self._url_to_title(url)
            posts.append({
                "url": url,
                "title": title or snippet[:80],
                "domain": domain,
                "snippet": snippet[:200] if snippet else "",
            })

        return sorted(posts, key=lambda x: len(x["snippet"]), reverse=True)[:12]

    async def _search_duckduckgo(self, query: str) -> list[str]:
        urls = []
        try:
            response = await self.client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query, "kl": "us-en"},
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.select("a.result__snippet, a.result__url"):
                    parent = link.find_parent("div", class_="result")
                    if parent:
                        a_tag = parent.select_one("a.result__a")
                        if a_tag:
                            href = a_tag.get("href", "")
                            if "uddg=" in href:
                                decoded = unquote(href.split("uddg=")[1].split("&")[0])
                                if decoded.startswith("http") and _safe_url(decoded):
                                    urls.append(decoded)
                            elif href.startswith("http") and _safe_url(href):
                                urls.append(href)
                for link in soup.select("a.result__a"):
                    href = link.get("href", "")
                    if "uddg=" in href:
                        decoded = unquote(href.split("uddg=")[1].split("&")[0])
                        if decoded.startswith("http") and _safe_url(decoded):
                            if decoded not in urls:
                                urls.append(decoded)
                    elif href.startswith("http") and _safe_url(href):
                        if href not in urls:
                            urls.append(href)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("DuckDuckGo search failed: %s", str(exc)[:100])
        return urls[:25]

    def _parse_search_results(self, urls: list[str], username: str) -> list[dict]:
        profiles = []
        seen: set[str] = set()

        for url in urls:
            domain = urlparse(url).netloc.lower().lstrip("www.")

            platform_name = None
            for known_domain, label in KNOWN_PLATFORMS.items():
                if known_domain in domain:
                    platform_name = label
                    break

            if platform_name is None or platform_name in seen:
                continue
            seen.add(platform_name)

            handle = username
            path = urlparse(url).path.strip("/")
            exclude = {"u", "user", "profile", "channel", "c", "in", "watch", "reel", "p",
                       "spaces", "posts", "embed", "reels"}
            parts = [p for p in path.split("/") if p and p not in exclude]
            for part in parts:
                if username.lower() in part.lower():
                    handle = part
                    break
            if handle == username and parts:
                candidate = parts[-1]
                if len(candidate) < 60 and not candidate.startswith("@"):
                    handle = candidate

            profiles.append({
                "platform": ".".join(domain.split(".")[-2:]),
                "label": platform_name,
                "handle": handle,
                "url": url,
            })

        return profiles

    def _already_in_known_platforms(self, domain: str) -> bool:
        for known in KNOWN_PLATFORMS:
            if known in domain:
                return True
        return False

    def _url_to_title(self, url: str) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip("/")
        if not path:
            return domain
        parts = path.split("/")
        meaningful = [p for p in parts if len(p) > 2 and not p.startswith("?")]
        if meaningful:
            return f"{domain} / ... / {meaningful[-1][:60]}"
        return domain

    def _extract_snippet_from_url(self, url: str, username: str) -> str:
        path = urlparse(url).path.lower()
        query_str = urlparse(url).query.lower()
        combined = f"{path} {query_str}"

        idx = combined.find(username.lower())
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(combined), idx + len(username) + 60)
            return combined[start:end]
        return combined[:100]


web_searcher = WebPresenceSearcher()
