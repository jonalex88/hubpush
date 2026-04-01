"""
Generate hashed user credentials for Vercel environment variables.

Usage:
  python generate_user_store.py

Output: two environment variable values to paste into Vercel project settings.

- HUBPUSH_AUTH_PEPPER: a random secret key used for HMAC hashing
- HUBPUSH_USERS_JSON:  JSON array of {username, pin_hash} — safe to store in env,
                       PINs cannot be reversed without the pepper

The hash formula matches api/v1/auth.js:
  HMAC-SHA256(key=pepper, message=username.lower() + ":" + pin)
"""
import argparse
import hashlib
import hmac
import json
import secrets

# ── User list ─────────────────────────────────────────────────────────────────
USERS = [
    ("Yusuf S",  "3856"),
    ("Michelle", "1937"),
    ("Meehgan",  "0946"),
    ("Jonathan", "3636"),
    ("AD",       "4837"),
    ("Cheslin",  "9742"),
]


def compute_hash(username: str, pin: str, pepper: str) -> str:
    """HMAC-SHA256 of 'username_lower:pin' — must match auth.js logic."""
    message = f"{username.lower()}:{pin}".encode("utf-8")
    return hmac.new(pepper.encode("utf-8"), message, hashlib.sha256).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate hashed user credentials for Vercel"
    )
    parser.add_argument(
        "--pepper",
        default="",
        help="HMAC pepper to use (auto-generated random value if omitted)",
    )
    args = parser.parse_args()

    pepper = args.pepper.strip() if args.pepper else secrets.token_urlsafe(32)

    users_list = [
        {
            "username": name,
            "pin_hash": compute_hash(name, pin, pepper),
        }
        for name, pin in USERS
    ]

    users_json = json.dumps(users_list, separators=(",", ":"))

    print("=" * 70)
    print("Copy the following into Vercel Environment Variables")
    print("(Project Settings → Environment Variables)")
    print("=" * 70)
    print()
    print("  Variable name : HUBPUSH_AUTH_PEPPER")
    print(f"  Value         : {pepper}")
    print()
    print("  Variable name : HUBPUSH_USERS_JSON")
    print(f"  Value         : {users_json}")
    print()
    print("=" * 70)
    print("After adding both variables, redeploy your Vercel project.")
    print()
    print("Test with:")
    print('  curl -X POST https://your-vercel-url.vercel.app/api/v1/auth \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -H "X-API-Key: <HUBPUSH_CLOUD_API_KEY>" \\')
    print('    -d \'{"username":"Yusuf S","pin":"3856"}\'')
    print("=" * 70)


if __name__ == "__main__":
    main()
