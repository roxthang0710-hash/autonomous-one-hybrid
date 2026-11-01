"""Verify Supabase Vault owner OAuth flow does not need GitHub secrets.

All credentials in these tests are fabricated, local-only and cannot access Meta.
"""
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from threads.credentials import load_credentials

NOW = datetime(2026, 11, 2, 10, tzinfo=timezone.utc)
LONG_TOKEN = "faux-" + ("v" * 65)
CHANNEL = {
    "status": "connected", "authorized": True, "auto_publish_enabled": True,
    "username": "dohay_dilam", "platform_user_id": "meta-234",
}


def row(days=40):
    return {
        "access_token": LONG_TOKEN, "verified_username": "dohay_dilam",
        "platform_user_id": "meta-234",
        "expires_at": (NOW + timedelta(days=days)).isoformat(),
        "enable_replies": False,
    }


class VaultOAuthTests(unittest.TestCase):
    def test_owner_oauth_starts_without_any_github_token_secret(self):
        db = MagicMock()
        db.request.side_effect = [[CHANNEL], [row()]]
        with patch.dict(os.environ, {
            "THREADS_PUBLISH_ENABLED": "",
            "THREADS_INITIAL_SHORT_TOKEN": "",
            "THREADS_TOKEN_KEY": "",
            "THREADS_EXPECTED_USERNAME": "",
        }):
            result = load_credentials(db, now=NOW)
        self.assertEqual(result, (LONG_TOKEN, "dohay_dilam"))
        paths = [c.args[1] for c in db.request.call_args_list]
        self.assertEqual(paths, ["/threads_channels", "/rpc/threads_read_vault_token"])

    def test_channel_must_be_owner_enabled_before_token_is_read(self):
        db = MagicMock()
        db.request.return_value = [dict(CHANNEL, auto_publish_enabled=False)]
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": ""}):
            self.assertIsNone(load_credentials(db, now=NOW))
        self.assertEqual(db.request.call_count, 1)

    def test_reject_token_for_different_meta_user(self):
        db = MagicMock()
        db.request.side_effect = [[CHANNEL], [dict(row(), platform_user_id="other")]]
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": ""}):
            with self.assertRaises(RuntimeError):
                load_credentials(db, now=NOW)

    def test_expired_owner_grant_does_not_auto_publish(self):
        db = MagicMock()
        db.request.side_effect = [[CHANNEL], [row(days=-2)]]
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": ""}):
            with self.assertRaises(RuntimeError):
                load_credentials(db, now=NOW)

    def test_renews_token_and_only_updates_service_role_vault(self):
        db = MagicMock()
        db.request.side_effect = [[CHANNEL], [row(days=3)], []]
        refreshed = "new-" + "z" * 65
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": ""}), \
             patch("threads.credentials._token_response",
                   return_value=(refreshed, 60*86400)) as meta, \
             patch("threads.credentials.verify_identity",
                   return_value=("dohay_dilam", "meta-234")):
            result = load_credentials(db, now=NOW)
        self.assertEqual(result[0], refreshed)
        self.assertEqual(meta.call_args.args[0], "/refresh_access_token")
        last = db.request.call_args
        self.assertEqual(last.args[1], "/rpc/threads_refresh_vault_token")
        self.assertEqual(last.kwargs["payload"]["p_platform_user_id"], "meta-234")


if __name__ == "__main__":
    unittest.main()
