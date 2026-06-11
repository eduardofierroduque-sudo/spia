from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import threading
import secrets
import hashlib


@dataclass
class UserAPIConfig:
    serpapi_key: str = ""
    google_cse_id: str = ""
    google_api_key: str = ""
    hibp_api_key: str = ""
    dehashed_api_key: str = ""
    dehashed_email: str = ""
    intelx_key: str = ""
    twitter_bearer_token: str = ""
    license_key: str = ""

    def any_search_configured(self) -> bool:
        return bool(self.serpapi_key or (self.google_api_key and self.google_cse_id))

    def any_breach_configured(self) -> bool:
        return bool(self.hibp_api_key or self.dehashed_api_key)


@dataclass
class LicenseInfo:
    key_hash: str = ""
    plan: str = "trial"  # trial, pro, enterprise
    expires_at: float = 0.0
    activated: bool = False

    def is_valid(self) -> bool:
        if not self.activated:
            return False
        if self.plan == "trial":
            return True
        if self.expires_at == 0:
            return True  # lifetime
        import time
        return time.time() < self.expires_at


class UserConfigStore:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._config: UserAPIConfig = UserAPIConfig()
        self._license: LicenseInfo = LicenseInfo()
        self._storage_path = Path(__file__).resolve().parent.parent.parent / "user_data"
        self._config_file = self._storage_path / "api_config.json"
        self._license_file = self._storage_path / "license.json"
        self._load()

    @classmethod
    def get_instance(cls) -> "UserConfigStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load(self):
        self._storage_path.mkdir(parents=True, exist_ok=True)
        if self._config_file.exists():
            try:
                data = json.loads(self._config_file.read_text())
                for k, v in data.items():
                    if hasattr(self._config, k):
                        setattr(self._config, k, v)
            except Exception:
                pass
        if self._license_file.exists():
            try:
                data = json.loads(self._license_file.read_text())
                self._license = LicenseInfo(**data)
            except Exception:
                pass

    def _save(self):
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(json.dumps(asdict(self._config), indent=2))
        self._license_file.write_text(json.dumps(asdict(self._license), indent=2))

    def get_config(self) -> UserAPIConfig:
        return self._config

    def update_config(self, **kwargs) -> UserAPIConfig:
        for k, v in kwargs.items():
            if hasattr(self._config, k) and v is not None:
                setattr(self._config, k, v)
        self._save()
        return self._config

    def get_license(self) -> LicenseInfo:
        return self._license

    def activate_license(self, key: str) -> LicenseInfo:
        valid_prefixes = {
            "SPIA-TRIAL-": ("trial", 14 * 86400),
            "SPIA-PRO-": ("pro", 365 * 86400),
            "SPIA-ENT-": ("enterprise", 0),
        }

        for prefix, (plan, duration) in valid_prefixes.items():
            if key.startswith(prefix):
                suffix = key[len(prefix):]
                try:
                    decoded = suffix.encode()
                    hash_check = hashlib.sha256(decoded).hexdigest()[:8]
                    if len(suffix) >= 8:
                        self._license.key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
                        self._license.plan = plan
                        self._license.expires_at = (__import__("time").time() + duration) if duration else 0
                        self._license.activated = True
                        self._save()
                        return self._license
                except Exception:
                    pass

        raise ValueError("Invalid license key")

    def deactivate(self):
        self._license = LicenseInfo()
        self._save()


user_config = UserConfigStore.get_instance()
