"""Offline tests for encrypted, renewable Threads Meta credentials."""
import hashlib
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet

from threads.credentials import load_credentials, verify_identity

NOW = datetime(2026, 11, 2, 8, tzinfo=timezone.utc)
KEY = Fernet.generate_key().decode("ascii")
BASE_ENV = {
    "THREADS_PUBLISH_ENABLED": "true",
    "THREADS_EXPECTED_USERNAME": "dohay_dilam",
    "THREADS_TOKEN_KEY": KEY,
    "THREADS_INITIAL_SHORT_TOKEN": "owner-granted-token",
    "THREADS_APP_SECRET": "server-secret",
}


def make_saved(expires_in_days=35, issued_days_ago=12, token="active-token"):
    issued = NOW - timedelta(days=issued_days_ago)
    return {
        "status": "active",
        "verified_username": "dohay_dilam",
        "platform_user_id": "meta-id-42",
        "ciphertext": Fernet(KEY.encode()).encrypt(token.encode()).decode(),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "issued_at": issued.isoformat(),
        "expires_at": (NOW + timedelta(days=expires_in_days)).isoformat(),
    }


class CredentialTests(unittest.TestCase):
    def test_off_until_explicit_approval(self):
        with patch.dict(os.environ, {**BASE_ENV, "THREADS_PUBLISH_ENABLED": "false"}):
            db = MagicMock()
            self.assertIsNone(load_credentials(db, now=NOW))
            db.request.assert_not_called()

    def test_unrecognized_username_not_authorized(self):
        with patch.dict(os.environ, {**BASE_ENV, "THREADS_EXPECTED_USERNAME": "other"}):
            db = MagicMock()
            self.assertIsNone(load_credentials(db, now=NOW))
            db.request.assert_not_called()

    def test_bootstrap_exchanges_short_for_long_and_only_stores_ciphertext(self):
        db = MagicMock()
        db.request.side_effect = [[], [{"brand_key": "do_hay_di_lam"}]]
        with patch.dict(os.environ, BASE_ENV), \
             patch("threads.credentials._token_response",
                   return_value=("renewed-long-token", 50 * 86400)), \
             patch("threads.credentials.verify_identity",
                   return_value=("dohay_dilam", "meta-id-42")):
            result = load_credentials(db, now=NOW)
        self.assertEqual(result, ("renewed-long-token", "dohay_dilam"))
        row = db.request.call_args.kwargs["payload"]
        self.assertNotIn("renewed-long-token", str(row))
        self.assertEqual(row["verified_username"], "dohay_dilam")
        self.assertNotEqual(row["ciphertext"], "renewed-long-token")

    def test_existing_token_is_decrypted_without_refresh_when_not_due(self):
        db = MagicMock()
        db.request.return_value = [make_saved(expires_in_days=35)]
        with patch.dict(os.environ, BASE_ENV), \
             patch("threads.credentials._token_response") as refresh:
            result = load_credentials(db, now=NOW)
        self.assertEqual(result, ("active-token", "dohay_dilam"))
        refresh.assert_not_called()

    def test_refresh_before_expiry_and_replace_only_ciphertext(self):
        db = MagicMock()
        db.request.side_effect = [[make_saved(expires_in_days=3)], []]
        with patch.dict(os.environ, BASE_ENV), \
             patch("threads.credentials._token_response",
                   return_value=("rotated-token", 60 * 86400)) as refresh, \
             patch("threads.credentials.verify_identity",
                   return_value=("dohay_dilam", "meta-id-42")):
            result = load_credentials(db, now=NOW)
        self.assertEqual(result, ("rotated-token", "dohay_dilam"))
        self.assertEqual(refresh.call_count, 1)
        args = refresh.call_args
        self.assertEqual(args.args[0], "/refresh_access_token")
        saved = db.request.call_args.kwargs["payload"]
        self.assertNotIn("rotated-token", str(saved))
        self.assertEqual(saved["status"], "active")

    def test_expired_token_does_not_post_or_auto_reauthorize(self):
        db = MagicMock()
        db.request.return_value = [make_saved(expires_in_days=-1)]
        with patch.dict(os.environ, BASE_ENV):
            with self.assertRaises(RuntimeError):
                load_credentials(db, now=NOW)

    def test_wrong_meta_identity_rejected(self):
        with patch("threads.credentials.thread_request",
                   return_value={"id": "42", "username": "other-brand"}):
            with self.assertRaises(ValueError):
                verify_identity("token", "dohay_dilam")

    def test_invalid_ciphertext_rejected(self):
        db = MagicMock()
        bad = make_saved()
        bad["ciphertext"] = "made-up-invalid-encrypted-string"
        db.request.return_value = [bad]
        with patch.dict(os.environ, BASE_ENV):
            with self.assertRaises(RuntimeError):
                load_credentials(db, now=NOW)


if __name__ == "__main__":
    unittest.main()
