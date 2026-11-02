"""Static regression guards for the SQL OAuth activation procedure.

Full SQL integration was also exercised on Supabase with a synthetic OAuth
session and disposable Vault secret in an exception-backed transaction that
rolls back all fake data. No production token or Meta API call is needed.
"""
import re
import unittest
from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "sql" / "v1_8_4_fix_oauth_activation.sql"


class ThreadsActivationSqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_row_number_casts_bigint_to_integer_before_date_arithmetic(self):
        self.assertRegex(self.sql, re.compile(
            r"\(\s*row_number\(\)\s+over\s*\(\s*order\s+by\s+"
            r"scheduled_at\s*,\s*created_at\s*,\s*id\s*\)\s*-\s*1\s*\)"
            r"\s*::\s*integer\s+as\s+n"
        ))
        self.assertIn("target_day + ordered.n", self.sql)

    def test_preserves_metricool_external_calendar_separation(self):
        self.assertIn("p.status='scheduled_external'", self.sql)
        self.assertIn("target_day := greatest(target_day", self.sql)
        self.assertIn("timezone 'asia/ho_chi_minh'", self.sql)

    def test_only_service_role_can_activate_account(self):
        self.assertIn("revoke all on function public.activate_threads_channel", self.sql)
        self.assertIn("from public,anon,authenticated;", self.sql)
        self.assertIn("to service_role;", self.sql)
        self.assertIn("if c.status='paused'", self.sql)
        self.assertIn("threads username mismatch", self.sql)
        self.assertIn("threads platform id mismatch", self.sql)


if __name__ == "__main__":
    unittest.main()
