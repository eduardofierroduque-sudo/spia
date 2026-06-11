from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "spia_worker",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
)


@celery_app.task(name="analyze_profile_task")
def analyze_profile_task(username: str, platform: str = "instagram"):
    from app.services.scanner import ProfileScanner
    from app.models.detector import BotDetector
    import asyncio

    async def _run():
        scanner = ProfileScanner()
        detector = BotDetector()
        profile = await scanner.fetch_profile(username, platform)
        if profile is None:
            return {"status": "error", "message": "Profile not found"}
        result = detector.predict(profile)
        return result.model_dump(mode="json")

    return asyncio.run(_run())
