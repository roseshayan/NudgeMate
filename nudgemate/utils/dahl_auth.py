import sys
import json
import random
import re
import urllib.request
import urllib.error
from http.cookiejar import CookieJar


def generate_username(email: str) -> str:
    """Generates a valid 3-20 character username from email."""
    local_part = email.split("@")[0] if "@" in email else email
    clean = re.sub(r"[^a-zA-Z0-9_]", "", local_part)
    if len(clean) < 3:
        clean = f"nudge_{clean}"
    clean = clean[:14]  # Leave room for 5 chars of random suffix
    rand_suffix = random.randint(1000, 9999)
    return f"{clean}_{rand_suffix}"


def create_and_setup_dahl_account(email: str, allocate_amount: int = 100_000_000) -> dict:
    """
    Registers a new account on inference.dahl.global,
    signs in to obtain session cookies,
    and allocates tokens from pool to the newly generated API key.
    """
    base_url = "https://inference.dahl.global/v1"
    headers = {
        "User-Agent": "NudgeMate-Installer/1.0",
        "Content-Type": "application/json",
    }

    # Step 1: Sign up
    user_info = None
    fingerprint = None
    api_key_data = None
    username = None

    for _ in range(3):
        username = generate_username(email)
        signup_payload = json.dumps({"username": username}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/auth/signup",
            data=signup_payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_info = data.get("user")
                fingerprint = data.get("fingerprint")
                api_key_data = data.get("api_key")
                if fingerprint and api_key_data:
                    break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            # If username is already taken, loop to try another random suffix
            if "taken" in err_body.lower() or e.code == 400:
                continue
            return {"success": False, "error": f"Signup HTTP {e.code}: {err_body}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error during signup: {str(e)}"}

    if not fingerprint or not api_key_data:
        return {"success": False, "error": "Failed to create Dahl account after multiple attempts."}

    token_str = api_key_data.get("token")
    key_id = api_key_data.get("id")

    # Step 2: Sign in to get session cookie
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    signin_payload = json.dumps({"fingerprint": fingerprint}).encode("utf-8")
    signin_req = urllib.request.Request(
        f"{base_url}/auth/signin",
        data=signin_payload,
        headers=headers,
        method="POST",
    )
    try:
        with opener.open(signin_req, timeout=15) as resp:
            pass
    except Exception as e:
        return {
            "success": True,
            "warning": f"Account created, but automatic signin failed ({str(e)}). You can manually allocate tokens at https://inference.dahl.global/account",
            "username": username,
            "fingerprint": fingerprint,
            "api_key": token_str,
            "allocated_tokens": 0,
        }

    # Step 3: Allocate tokens from pool to key
    allocate_payload = json.dumps({
        "key_id": key_id,
        "amount": allocate_amount,
    }).encode("utf-8")
    allocate_req = urllib.request.Request(
        f"{base_url}/account/allocate",
        data=allocate_payload,
        headers=headers,
        method="POST",
    )

    allocated_tokens = 0
    try:
        with opener.open(allocate_req, timeout=15) as resp:
            allocated_tokens = allocate_amount
    except Exception as e:
        # Allocation might fail if pool balance has delay, but account is still valid
        pass

    return {
        "success": True,
        "username": username,
        "fingerprint": fingerprint,
        "api_key": token_str,
        "key_id": key_id,
        "allocated_tokens": allocated_tokens,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Email argument is required"}))
        sys.exit(1)

    email_arg = sys.argv[1]
    result = create_and_setup_dahl_account(email_arg)
    print(json.dumps(result, ensure_ascii=False))
