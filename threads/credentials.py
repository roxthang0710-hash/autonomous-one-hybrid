"""Encrypted long-lived Threads token lifecycle for unattended GitHub Actions.

User-granted short-lived token is exchanged ONCE for a long-lived token.
Only ciphertext is stored in Supabase. GitHub Secret THREADS_TOKEN_KEY is required.
Never log tokens, passwords, raw OAuth codes or the key.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import requests
from cryptography.fernet import Fernet, InvalidToken

from threads.brand import BRAND_KEY
from threads.publisher import thread_request  # read-only /me; avoids writing posts

API = "https://graph.threads.net"
EXPECTED = "dohay_dilam"
REFRESH_BEFORE = timedelta(days=14)
MIN_AGE_FOR_REFRESH = timedelta(hours=25)
MAX_TOKEN_AGE = timedelta(days=60)


def _key():
    raw = os.getenv("THREADS_TOKEN_KEY", "").strip()
    if not raw:
        return None
    try:
        return Fernet(raw.encode("ascii"))
    except (ValueError, TypeError):
        raise RuntimeError("THREADS_TOKEN_KEY must be a Fernet base64 key") from None


def _expected():
    name = os.getenv("THREADS_EXPECTED_USERNAME", "").strip().lstrip("@").casefold()
    return name if name == EXPECTED else None


def _token_response(path, *, token, method="GET", secret=None, params=None, fetch=None):
    request = fetch or (requests.post if method == "POST" else requests.get)
    values = dict(params or {})
    if method == "GET":
        values["access_token"] = token
        response = request(API + path, params=values, timeout=20)
    else:
        response = request(API + path, data=values, timeout=20)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("access_token"), str):
        raise ValueError("Unexpected Meta token response")
    lifetime = body.get("expires_in")
    if type(lifetime) is not int or not 3600 <= lifetime <= 70 * 86400:
        raise ValueError("Meta response missing valid token expiry")
    return body["access_token"], lifetime


def verify_identity(token, expected, *, read=None):
    read = read or thread_request
    profile = read("GET", "/me", token, params={"fields": "id,username"})
    username = str(profile.get("username") or "").casefold()
    user_id = str(profile.get("id") or "")
    if username != expected or not user_id:
        raise ValueError("Meta token does not match brand owner")
    return username, user_id


def _save(db, fernet, token, lifetime, username, user_id, now, *, refreshed=False):
    # All writes are ciphertext. Hash allows audit comparison without leaking token.
    row = {
        "brand_key": BRAND_KEY,
        "ciphertext": fernet.encrypt(token.encode("utf-8")).decode("ascii"),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "verified_username": username,
        "platform_user_id": user_id,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=lifetime)).isoformat(),
        "refreshed_at": now.isoformat() if refreshed else None,
        "status": "active", "last_error_code": None,
        "updated_at": now.isoformat(),
    }
    db.request("POST", "/threads_connection_tokens",
               params={"on_conflict": "brand_key"},
               payload=row, prefer="resolution=merge-duplicates,return=representation")


def _read(db):
    rows = db.request("GET", "/threads_connection_tokens", params={
        "select": "ciphertext,verified_username,platform_user_id,"
                  "issued_at,expires_at,status,token_sha256",
        "brand_key": "eq." + BRAND_KEY, "limit": "1",
    })
    return rows[0] if rows else None


def _validate_db_row(record, expected, fernet, now):
    if record["status"] != "active" or record["verified_username"] != expected:
        raise RuntimeError("Stored Threads token is revoked, expired or wrong account")
    try:
        issued = datetime.fromisoformat(record["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        token = fernet.decrypt(record["ciphertext"].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError, KeyError):
        raise RuntimeError("Invalid encrypted Threads token; authorization stopped") from None
    if hashlib.sha256(token.encode()).hexdigest() != record["token_sha256"]:
        raise RuntimeError("Threads token integrity check failed")
    if issued.tzinfo is None or expires.tzinfo is None or expires <= now:
        raise RuntimeError("Stored Threads token has expired")
    if issued > now + timedelta(minutes=5):
        raise RuntimeError("Token time metadata invalid")
    return token, issued, expires



def _vault_credentials(db, expected, now, *, refresh=True):
    """Read owner-authorized token from Supabase Vault, not a plaintext table.

    A completed OAuth callback atomically sets the channel's authorized switch
    and keeps token encrypted at rest. There is no manual GitHub secret step.
    """
    channels = db.request("GET", "/threads_channels", params={
        "select": "username,platform_user_id,status,authorized,auto_publish_enabled",
        "brand_key": "eq." + BRAND_KEY, "limit": "1",
    })
    if not channels:
        return None
    channel = channels[0]
    if channel.get("status") != "connected" or not channel.get("authorized") or \
       not channel.get("auto_publish_enabled") or \
       channel.get("username") != expected or \
       not channel.get("platform_user_id"):
        return None
    result = db.request("POST", "/rpc/threads_read_vault_token",
                        payload={"p_brand_key": BRAND_KEY})
    if not result:
        return None
    row = result[0]
    if str(row.get("verified_username") or "") != expected or \
       str(row.get("platform_user_id") or "") != str(channel["platform_user_id"]):
        raise RuntimeError("Supabase Vault Meta identity mismatch")
    token = str(row.get("access_token") or "")
    if len(token) < 40:
        raise RuntimeError("Invalid stored Threads token")
    try:
        expiry = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError, KeyError):
        raise RuntimeError("Invalid Threads token expiration") from None
    if expiry.tzinfo is None or now >= expiry:
        raise RuntimeError("Threads authorization expired; reauthorize through owner portal")
    if refresh and expiry - now < REFRESH_BEFORE:
        # This access token is already long-lived. Meta allows refreshing
        # valid tokens, provided they have aged enough since issue/last refresh.
        # The endpoint may temporarily fail; if token is still valid, safely
        # keep existing credentials until the next automatic attempt.
        try:
            refreshed, lifetime = _token_response(
                "/refresh_access_token", token=token,
                params={"grant_type": "th_refresh_token"})
            username, user_id = verify_identity(refreshed, expected)
            if user_id != str(row["platform_user_id"]):
                raise RuntimeError("Meta OAuth account changed during refresh")
            db.request("POST", "/rpc/threads_refresh_vault_token", payload={
                "p_brand_key": BRAND_KEY,
                "p_platform_user_id": user_id,
                "p_new_token": refreshed,
                "p_new_expiry": (datetime.now(timezone.utc) +
                                 timedelta(seconds=lifetime)).isoformat(),
            })
            token = refreshed
        except requests.RequestException:
            if expiry - now < timedelta(days=1):
                raise RuntimeError("Meta token refresh failed near expiry") from None
        except ValueError:
            if expiry - now < timedelta(days=1):
                raise RuntimeError("Meta token refresh returned invalid data") from None
    return token, expected


def load_credentials(db, *, now=None, refresh=True):
    """Return verified token, username or None. No external action without owner switch.

    First-time bootstrap requires:
      THREADS_INITIAL_SHORT_TOKEN (owner-granted Meta short-lived token)
      THREADS_APP_SECRET (real Threads App Secret, GitHub Secret only)
      THREADS_TOKEN_KEY (unique Fernet key, GitHub Secret only).
    """
    now = now or datetime.now(timezone.utc)
    # Preferred production route: verified owner portal -> encrypted Vault.
    # No GH secrets are required after the owner has completed OAuth.
    vaulted = _vault_credentials(db, EXPECTED, now, refresh=refresh)
    if vaulted is not None:
        return vaulted

    # Legacy operator route remains disabled until its own explicit switch.
    if os.getenv("THREADS_PUBLISH_ENABLED", "").casefold() != "true":
        return None
    expected = _expected()
    fernet = _key()
    if not expected or not fernet:
        return None
    saved = _read(db)
    if not saved:
        initial = os.getenv("THREADS_INITIAL_SHORT_TOKEN", "").strip()
        app_secret = os.getenv("THREADS_APP_SECRET", "").strip()
        if not initial or not app_secret:
            return None
        # Exchange before storing. This is not a direct login or permission bypass.
        long_token, duration = _token_response(
            "/access_token", token=initial,
            params={"grant_type": "th_exchange_token", "client_secret": app_secret})
        username, user_id = verify_identity(long_token, expected)
        _save(db, fernet, long_token, duration, username, user_id, now)
        return long_token, expected
    token, issued, expires = _validate_db_row(saved, expected, fernet, now)
    if refresh and expires - now <= REFRESH_BEFORE:
        if now - issued < MIN_AGE_FOR_REFRESH:
            # Token has not aged sufficiently for refresh. It still works.
            return token, expected
        new_token, duration = _token_response(
            "/refresh_access_token", token=token,
            params={"grant_type": "th_refresh_token"})
        username, user_id = verify_identity(new_token, expected)
        if user_id != saved["platform_user_id"]:
            raise RuntimeError("Threads refresh returned a different account")
        _save(db, fernet, new_token, duration, username, user_id, now, refreshed=True)
        return new_token, expected
    return token, expected
