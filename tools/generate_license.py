import secrets
import hashlib
import argparse
import sys
from datetime import datetime, timedelta

PREFIXES = {
    "trial": ("SPIA-TRIAL-", 14),
    "pro": ("SPIA-PRO-", 365),
    "enterprise": ("SPIA-ENT-", 0),
}


def generate_key(plan: str) -> str:
    if plan not in PREFIXES:
        raise ValueError(f"Unknown plan: {plan}. Use: trial, pro, enterprise")

    prefix, days = PREFIXES[plan]
    random_part = secrets.token_urlsafe(24)[:24]
    key = f"{prefix}{random_part}"

    hash_check = hashlib.sha256(key.encode()).hexdigest()[:8]
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d") if days else "never"

    return {
        "key": key,
        "plan": plan.upper(),
        "hash": hash_check,
        "expires": expires,
        "days": days if days else "lifetime",
    }


def main():
    parser = argparse.ArgumentParser(description="SPIA License Key Generator")
    parser.add_argument("plan", choices=["trial", "pro", "enterprise"], help="License plan")
    parser.add_argument("--count", type=int, default=1, help="Number of keys to generate")
    parser.add_argument("--output", type=str, help="Output file (optional)")
    args = parser.parse_args()

    keys = []
    for _ in range(args.count):
        k = generate_key(args.plan)
        keys.append(k)
        print(f"Plan     : {k['plan']}")
        print(f"Key      : {k['key']}")
        print(f"Hash     : {k['hash']}")
        print(f"Expires  : {k['expires']}")
        print("-" * 50)

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(keys, f, indent=2)
        print(f"\nSaved {len(keys)} keys to {args.output}")

    if args.count == 1:
        print(f"\nDefault trial keys (use for testing):")
        for p, (prefix, _) in PREFIXES.items():
            k = generate_key(p)
            print(f"  {k['plan']}: {k['key']}")


if __name__ == "__main__":
    main()
