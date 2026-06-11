import hashlib
import secrets
import json
import sys
from datetime import datetime

PREFIXES = {
    "SPIA-TRIAL-": ("trial", 14 * 86400),
    "SPIA-PRO-": ("pro", 365 * 86400),
    "SPIA-ENT-": ("enterprise", 0),
}


def validate_key(key: str) -> dict | None:
    for prefix, (plan, duration) in PREFIXES.items():
        if key.startswith(prefix):
            suffix = key[len(prefix):]
            if len(suffix) >= 8:
                hash_check = hashlib.sha256(key.encode()).hexdigest()[:8]
                expires = (datetime.now().timestamp() + duration) if duration else 0
                return {
                    "valid": True,
                    "plan": plan,
                    "expires_at": expires,
                    "hash": hash_check,
                }
    return None


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else input("Enter license key: ").strip()
    result = validate_key(key)
    if result:
        print(json.dumps(result, indent=2))
        from datetime import datetime as dt
        if result["expires_at"]:
            exp = dt.fromtimestamp(result["expires_at"])
            print(f"Expires: {exp.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("Expires: Lifetime")
    else:
        print("Invalid license key")
