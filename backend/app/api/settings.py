from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.core.user_config import user_config, UserAPIConfig, LicenseInfo

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class APIConfigRequest(BaseModel):
    serpapi_key: str | None = None
    google_cse_id: str | None = None
    google_api_key: str | None = None
    hibp_api_key: str | None = None
    dehashed_api_key: str | None = None
    dehashed_email: str | None = None
    intelx_key: str | None = None
    twitter_bearer_token: str | None = None


class LicenseRequest(BaseModel):
    license_key: str


class ConfigStatusResponse(BaseModel):
    apis: dict
    license: dict
    features: dict


@router.get("/status", response_model=ConfigStatusResponse)
async def get_config_status():
    cfg = user_config.get_config()
    lic = user_config.get_license()

    return ConfigStatusResponse(
        apis={
            "serpapi": bool(cfg.serpapi_key),
            "google_search": bool(cfg.google_api_key and cfg.google_cse_id),
            "hibp": bool(cfg.hibp_api_key),
            "dehashed": bool(cfg.dehashed_api_key and cfg.dehashed_email),
            "intelx": bool(cfg.intelx_key),
            "twitter": bool(cfg.twitter_bearer_token),
            "any_search": cfg.any_search_configured(),
            "any_breach": cfg.any_breach_configured(),
        },
        license={
            "plan": lic.plan,
            "activated": lic.activated,
            "valid": lic.is_valid(),
            "expires_at": lic.expires_at if lic.expires_at else None,
        },
        features={
            "deep_web_search": cfg.any_search_configured(),
            "breach_api": cfg.any_breach_configured(),
            "dark_web_intelx": bool(cfg.intelx_key),
            "social_scan": bool(cfg.twitter_bearer_token),
        },
    )


@router.put("/apis")
async def update_api_config(body: APIConfigRequest):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    cfg = user_config.update_config(**updates)
    masked = {k: "***" + v[-4:] if v and len(v) > 4 else "" for k, v in cfg.__dict__.items() if k in updates}
    return {"status": "ok", "updated": list(updates.keys()), "masked": masked}


@router.post("/license/activate")
async def activate_license(body: LicenseRequest):
    try:
        lic = user_config.activate_license(body.license_key)
        return {
            "status": "ok",
            "plan": lic.plan,
            "expires_at": lic.expires_at if lic.expires_at else "lifetime",
            "message": f"License activated — {lic.plan.upper()} plan",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/license/deactivate")
async def deactivate_license():
    user_config.deactivate()
    return {"status": "ok", "message": "License deactivated"}
