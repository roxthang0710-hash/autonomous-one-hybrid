import unittest
from unittest.mock import patch
import requests
import agent

class AgentTests(unittest.TestCase):
    def test_topics_are_defined(self):
        self.assertGreater(len(agent.TOPICS), 0)

    def test_research_failure_returns_no_sources(self):
        with patch("agent.requests.get", side_effect=requests.RequestException("offline")):
            self.assertEqual(agent.research("small business"), [])

    def test_output_schema_needs_approval(self):
        self.assertIn("needs_owner_approval", agent.SCHEMA["required"])
        self.assertFalse(agent.SCHEMA["additionalProperties"])

    def test_secret_is_required(self):
        with patch.dict("os.environ", {"TEST_MISSING_KEY": ""}):
            with self.assertRaises(RuntimeError):
                agent.require_env("TEST_MISSING_KEY")

if __name__ == "__main__":
    unittest.main()
