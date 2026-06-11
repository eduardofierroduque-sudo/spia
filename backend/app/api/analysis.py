import logging
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.security import is_internal_url, InputSanitizer, audit_logger
from app.core.user_config import user_config
from app.models.schemas import PrivacyRequest, PrivacyResponse, PrivacyReport
from app.services.privacy_scanner import privacy_scanner, detect_query_type

logger = logging.getLogger("spia")
router = APIRouter(prefix="/api/v1", tags=["privacy"])

SAFE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/avif", "image/svg+xml", "image/bmp", "image/tiff",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def validate_image_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL: must use HTTP or HTTPS")
    if len(url) > 2048:
        raise HTTPException(status_code=400, detail="URL too long")
    if is_internal_url(url):
        raise HTTPException(status_code=403, detail="Forbidden URL (internal address)")
    if not url.startswith("https://"):
        logger.warning("Image proxy served non-HTTPS URL from=%s", url[:80])
    return url


@router.post("/scan", response_model=PrivacyResponse)
async def scan_privacy(request: PrivacyRequest, req: Request):
    settings = get_settings()
    client_ip = req.client.host if req.client else "unknown"

    query = request.query.strip()
    if InputSanitizer.detect_attack(query):
        audit_logger.log("blocked_attack", client_ip, "XSS/SQLi detected in scan query", query)
        raise HTTPException(status_code=400, detail="Query contains forbidden characters")

    if len(query) < settings.min_query_length:
        raise HTTPException(status_code=400, detail="Query is too short")
    if len(query) > settings.max_query_length:
        raise HTTPException(status_code=400, detail="Query is too long")

    query = InputSanitizer.sanitize(query, max_length=settings.max_query_length)
    if not query:
        raise HTTPException(status_code=400, detail="Invalid query after sanitization")

    qtype = request.query_type if request.query_type != "auto" else detect_query_type(query)
    if qtype not in ("email", "phone", "username", "name"):
        qtype = "auto"
        qtype = detect_query_type(query)

    audit_logger.log("scan_started", client_ip, f"type={qtype}", query)

    data = await privacy_scanner.scan(query, qtype)

    lic = user_config.get_license()
    if not lic.is_valid():
        data["recommendations"].insert(0,
            "Using limited DuckDuckGo mode. Activate a license and configure API keys in Settings for full results."
        )

    report = PrivacyReport(
        id=uuid4(),
        query=query,
        query_type=qtype,
        privacy_score=data["privacy_score"],
        total_exposures=data["total_exposures"],
        exposures=data["exposures"],
        images=data.get("images", []),
        categories=data["categories"],
        data_sources=data["data_sources"],
        recommendations=data.get("recommendations", []),
    )

    audit_logger.log("scan_completed", client_ip, f"score={report.privacy_score}", query)
    return PrivacyResponse(status="completed", report=report)


@router.get("/image-proxy")
async def image_proxy(
    url: str = Query(..., min_length=10, max_length=2048),
    req: Request = None,
):
    validated_url = validate_image_url(url)

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=5.0),
            follow_redirects=True,
            max_redirects=3,
        ) as client:
            resp = await client.get(
                validated_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            if resp.status_code == 200:
                ct = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                if ct not in SAFE_CONTENT_TYPES:
                    raise HTTPException(status_code=415, detail="Unsupported content type")

                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > MAX_IMAGE_SIZE:
                    raise HTTPException(status_code=413, detail="Image too large")

                body = b""
                chunk_count = 0
                async for chunk in resp.aiter_bytes(chunk_size=8192):
                    body += chunk
                    chunk_count += 1
                    if len(body) > MAX_IMAGE_SIZE or chunk_count > 1024:
                        raise HTTPException(status_code=413, detail="Image too large")

                return StreamingResponse(
                    content=iter([body]),
                    media_type=ct,
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "X-Content-Type-Options": "nosniff",
                    },
                )

            logger.warning("Image proxy upstream returned %d for %s", resp.status_code, validated_url[:80])
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except httpx.TooManyRedirects:
        raise HTTPException(status_code=502, detail="Too many redirects")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Could not connect to remote server")
    except Exception as exc:
        logger.error("Image proxy error for %s: %s", validated_url[:80], str(exc)[:200])

    raise HTTPException(status_code=404, detail="Image not available")


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "spia-privacy"}
