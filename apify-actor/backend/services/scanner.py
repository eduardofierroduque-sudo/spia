import asyncio
import json
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from app.core.security import is_internal_url
from app.features.extractor import FeatureExtractor
from app.models.schemas import ProfileData
from app.services.web_search import web_searcher

logger = logging.getLogger("spia")

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)
PHONE_REGEX = re.compile(
    r'\+?[\d]{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,6}'
)
URL_REGEX = re.compile(
    r'(?:https?://[^\s]+|[\w-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)'
)

PLATFORM_PATTERNS: dict[str, str] = {
    "youtube": r'(?:youtube\.com|youtu\.be)/(?:@|channel/|c/|user/)?([\w-]+)',
    "itch.io": r'(?:https?://)?([\w-]+)\.itch\.io',
    "github": r'github\.com/([\w-]+)',
    "twitter": r'(?:twitter\.com|x\.com)/([\w-]+)',
    "tiktok": r'tiktok\.com/@([\w.]+)',
    "twitch": r'twitch\.tv/([\w-]+)',
    "linkedin": r'linkedin\.com/in/([\w-]+)',
    "discord": r'discord(?:\.gg|\.com/invite)/([\w-]+)',
    "linktree": r'linktr\.ee/([\w-]+)',
    "behance": r'behance\.net/([\w-]+)',
    "medium": r'medium\.com/@([\w-]+)',
    "patreon": r'patreon\.com/([\w-]+)',
    "reddit": r'reddit\.com/(?:u|user)/([\w-]+)',
    "steam": r'steamcommunity\.com/id/([\w-]+)',
    "spotify": r'open\.spotify\.com/(?:artist|user)/([\w-]+)',
}

PLATFORM_LABELS: dict[str, str] = {
    "youtube": "YouTube",
    "itch.io": "itch.io",
    "github": "GitHub",
    "twitter": "X / Twitter",
    "tiktok": "TikTok",
    "twitch": "Twitch",
    "linkedin": "LinkedIn",
    "discord": "Discord",
    "linktree": "Linktree",
    "behance": "Behance",
    "medium": "Medium",
    "patreon": "Patreon",
    "reddit": "Reddit",
    "steam": "Steam",
    "spotify": "Spotify",
}


def extract_public_contact(bio: str) -> tuple[str, str, str]:
    if not bio:
        return "", "", ""
    email_match = EMAIL_REGEX.search(bio)
    phone_match = PHONE_REGEX.search(bio)
    url_match = URL_REGEX.search(bio)
    return (
        email_match.group(0) if email_match else "",
        phone_match.group(0) if phone_match else "",
        url_match.group(0) if url_match else "",
    )


def extract_associated_platforms(text: str, external_url: str = "") -> list[dict]:
    combined = f"{text} {external_url}"
    seen = set()
    platforms = []
    for key, pattern in PLATFORM_PATTERNS.items():
        match = re.search(pattern, combined, re.IGNORECASE)
        if match and match.group(1) not in seen:
            handle = match.group(1).rstrip('/')
            seen.add(handle)
            platforms.append({
                "platform": key,
                "label": PLATFORM_LABELS.get(key, key),
                "handle": handle,
                "url": "",
            })
    return platforms


def compute_activity(
    post_count: int, account_age_days: int, last_post_days: int
) -> tuple[bool, str, float]:
    if post_count == 0:
        return False, "sin posts", 0.0
    if last_post_days >= 999:
        return True, "activa (sin fecha)", post_count / max(account_age_days, 1) * 7
    if last_post_days > 365:
        return False, "abandonada", 0.0
    if last_post_days > 90:
        return False, "inactiva", 0.0
    if last_post_days > 30:
        return True, "poco activa", post_count / max(account_age_days, 1) * 7
    if last_post_days > 7:
        return True, "activa", post_count / max(account_age_days, 1) * 7
    if last_post_days > 2:
        return True, "muy activa", post_count / max(account_age_days, 1) * 7
    return True, "hiperactiva", post_count / max(account_age_days, 1) * 7


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "X-IG-App-ID": "936619743392459",
    "X-ASBD-ID": "198387",
    "Origin": "https://www.instagram.com",
    "Referer": "https://www.instagram.com/",
    "Sec-Fetch-Site": "same-origin",
}


class ProfileScanner:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            http2=True,
            max_redirects=5,
        )
        self.platform_adapters = {
            "instagram": self._fetch_instagram,
            "twitter": self._fetch_twitter,
            "tiktok": self._fetch_tiktok,
        }

    async def fetch_profile(
        self, username: str, platform: str
    ) -> Optional[ProfileData]:
        username = username.strip().replace('@', '').split('?')[0].rstrip('/')
        if len(username) > 100:
            return None
        adapter = self.platform_adapters.get(platform)
        if adapter is None:
            return None
        profile = None
        try:
            profile = await adapter(username)
            if profile is not None:
                profile.data_source = "real"
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Profile fetch %s/%s failed: %s", platform, username[:30], str(exc)[:100])

        if profile is None:
            profile = self._mock_profile(username, platform)

        try:
            web_results, posts = await asyncio.gather(
                web_searcher.search(username, platform),
                web_searcher.search_posts(username),
                return_exceptions=True,
            )
            if not isinstance(web_results, Exception):
                profile.web_presence = web_results
            if not isinstance(posts, Exception) and posts:
                profile.posts_found = posts
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Web search for %s failed: %s", username[:30], str(exc)[:100])

        return profile

    async def _fetch_instagram(self, username: str) -> Optional[ProfileData]:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        try:
            response = await self.client.get(url, headers=API_HEADERS)
            if response.status_code == 200:
                data = response.json()
                user = data.get("data", {}).get("user", {})
                if user:
                    return self._parse_instagram_user(user, username)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Instagram API fetch failed for %s: %s", username, str(exc)[:100])

        try:
            response = await self.client.get(
                f"https://www.instagram.com/{username}/",
                headers=BROWSER_HEADERS,
            )
            if response.status_code == 200:
                profile = self._parse_instagram_html(response.text, username)
                if profile is not None:
                    return profile
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Instagram HTML scrape failed for %s: %s", username, str(exc)[:100])

        try:
            response = await self.client.get(
                f"https://www.instagram.com/{username}/embed/",
                headers=BROWSER_HEADERS,
            )
            if response.status_code == 200:
                profile = self._parse_instagram_html(response.text, username)
                if profile is not None:
                    return profile
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Instagram embed scrape failed for %s: %s", username, str(exc)[:100])

        return None

    def _parse_instagram_user(self, user: dict, username: str) -> ProfileData:
        bio_text = user.get("biography", "") or ""
        email, phone, url = extract_public_contact(bio_text)
        ext_url = user.get("external_url", "") or ""

        post_count = user.get("media_count", 0) or user.get("edge_owner_to_timeline_media", {}).get("count", 0)
        followers = user.get("follower_count", 0) or user.get("edge_followed_by", {}).get("count", 0)
        following = user.get("following_count", 0) or user.get("edge_follow", {}).get("count", 0)

        account_age_days = 365
        last_post_days = 999

        is_active, activity_level, posts_per_week = compute_activity(
            post_count, account_age_days, last_post_days
        )

        associated = extract_associated_platforms(bio_text, ext_url)

        return ProfileData(
            id=uuid4(),
            username=user.get("username", username),
            platform="instagram",
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            account_age_days=account_age_days,
            has_profile_pic=bool(user.get("profile_pic_url") or user.get("profile_pic_url_hd")),
            has_bio=bool(bio_text),
            has_external_url=bool(ext_url),
            is_verified=user.get("is_verified", False),
            is_business=user.get("is_business_account", False),
            bio_length=len(bio_text),
            bio_text=bio_text,
            public_email=email,
            public_phone=phone,
            external_url=ext_url,
            is_active=is_active,
            last_post_days_ago=last_post_days,
            posts_per_week=posts_per_week,
            activity_level=activity_level,
            default_profile_pic=False,
            associated_platforms=associated,
            data_source="real",
        )

    def _parse_instagram_html(self, html: str, username: str) -> Optional[ProfileData]:
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>',
            r'window\.___INITIAL_STATE__\s*=\s*({.*?});\s*</script>',
            r'__NEXT_DATA__\s*=\s*({.*?});\s*</script>',
            r'"user":\s*({[^}]*"username":\s*"[^"]*"[^}]*})',
            r'"graphql":\s*({[^}]*"user":\s*{[^}]*}[^}]*})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    raw = match.group(1)
                    data = json.loads(raw)

                    for path in [
                        ["user"],
                        ["props", "pageProps", "user"],
                        ["states", 0, "data"],
                    ]:
                        user = data
                        try:
                            for key in path:
                                user = user.get(key, {}) if isinstance(user, dict) else user[key]
                        except (KeyError, IndexError, TypeError):
                            continue
                        if isinstance(user, dict) and user.get("username"):
                            return self._parse_instagram_user(user, username)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

        bio_match = re.search(
            r'<meta\s+name="description"\s+content="([^"]*)"',
            html, re.IGNORECASE,
        )
        bio_text = ""
        if bio_match:
            desc = bio_match.group(1)
            parts = desc.split(" on Instagram:")[0] if " on Instagram:" in desc else desc
            bio_text = parts.split(" - ")[1] if " - " in parts else ""

        followers_match = re.search(r'([\d,.]+[KM]?)\s*Followers', html)
        following_match = re.search(r'([\d,.]+[KM]?)\s*Following', html)
        posts_match = re.search(r'([\d,.]+[KM]?)\s*Posts', html)

        def parse_count(raw: Optional[str]) -> int:
            if not raw:
                return 0
            raw = raw.replace(',', '')
            if raw.endswith('K'):
                return int(float(raw[:-1]) * 1000)
            if raw.endswith('M'):
                return int(float(raw[:-1]) * 1000000)
            return int(raw)

        followers = parse_count(followers_match.group(1) if followers_match else None)
        following = parse_count(following_match.group(1) if following_match else None)
        post_count = parse_count(posts_match.group(1) if posts_match else None)

        if not bio_text and followers == 0:
            return None

        email, phone, url = extract_public_contact(bio_text)
        ext_url = url
        url_in_bio = re.search(
            r'<a[^>]*href="([^"]*)"[^>]*rel="me"[^>]*>',
            html, re.IGNORECASE,
        )
        if url_in_bio:
            ext_url = url_in_bio.group(1)

        is_active, activity_level, posts_per_week = compute_activity(
            post_count, 365, 999
        )

        associated = extract_associated_platforms(bio_text, ext_url)

        return ProfileData(
            id=uuid4(),
            username=username,
            platform="instagram",
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            account_age_days=365,
            has_profile_pic=True,
            has_bio=bool(bio_text),
            has_external_url=bool(ext_url),
            is_verified=False,
            is_business=False,
            bio_length=len(bio_text),
            bio_text=bio_text,
            public_email=email,
            public_phone=phone,
            external_url=ext_url,
            is_active=is_active,
            last_post_days_ago=999,
            posts_per_week=posts_per_week,
            activity_level=activity_level,
            default_profile_pic=False,
            associated_platforms=associated,
            data_source="real",
        )

    async def _fetch_twitter(self, username: str) -> Optional[ProfileData]:
        return self._mock_profile(username, "twitter")

    async def _fetch_tiktok(self, username: str) -> Optional[ProfileData]:
        return self._mock_profile(username, "tiktok")

    def _mock_profile(self, username: str, platform: str) -> ProfileData:
        account_age = random.randint(1, 1500)
        followers = random.randint(0, 10000)
        following = random.randint(0, 5000)
        post_count = random.randint(0, 500)
        last_post_days = random.randint(0, 400)

        mock_bios = [
            "DM for collabs",
            "Barcelona | contact@example.com",
            "Developer & Designer",
            "Travel | Food | contact@spia.io",
            "+34 600 123 456 WhatsApp",
            "",
            "Photography | contact@fotografo.com | linktr.ee/profile",
            "Fashion | brand@company.es",
        ]
        bio_text = random.choice(mock_bios)
        email, phone, url = extract_public_contact(bio_text)

        is_active, activity_level, posts_per_week = compute_activity(
            post_count, account_age, last_post_days
        )

        profile = ProfileData(
            id=uuid4(),
            username=username,
            platform=platform,
            follower_count=followers,
            following_count=following,
            post_count=post_count,
            account_age_days=account_age,
            has_profile_pic=random.random() > 0.2,
            has_bio=bool(bio_text),
            has_external_url=bool(url),
            is_verified=random.random() > 0.95,
            is_business=random.random() > 0.8,
            bio_length=len(bio_text),
            bio_text=bio_text,
            public_email=email,
            public_phone=phone,
            external_url=url,
            is_active=is_active,
            last_post_days_ago=last_post_days,
            posts_per_week=posts_per_week,
            activity_level=activity_level,
            avg_post_interval_hours=random.uniform(1, 168),
            post_like_avg=random.uniform(0, followers * 0.1),
            post_comment_avg=random.uniform(0, followers * 0.02),
            follower_growth_rate=random.uniform(0, 200),
            following_growth_rate=random.uniform(0, 100),
            username_entropy=FeatureExtractor.compute_username_entropy(username),
            digit_ratio_in_username=FeatureExtractor.compute_digit_ratio(username),
            default_profile_pic=random.random() > 0.85,
            posts_with_hashtags_ratio=random.uniform(0, 1),
            unique_hashtags_ratio=random.uniform(0, 1),
            posts_with_mentions_ratio=random.uniform(0, 0.5),
            caption_similarity_score=random.uniform(0, 1),
            engagement_rate=0.0,
            follow_ratio=0.0,
            associated_platforms=[],
            data_source="mock",
        )

        FeatureExtractor.compute_derived_features(profile)
        return profile
