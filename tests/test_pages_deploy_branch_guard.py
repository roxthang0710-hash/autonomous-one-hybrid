"""Guard production GitHub Pages deployment from feature-branch pushes.

This regression test checks the workflow source without adding third-party
YAML dependencies to Enna's CI pipeline.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "threads-pages.yml"


class PagesDeployBranchGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = WORKFLOW.read_text(encoding="utf-8")

    def test_push_only_from_main(self):
        self.assertIn("  push:\n    branches: [main]\n    paths:", self.config)

    def test_no_feature_branch_manual_deploy(self):
        self.assertIn("github.ref == 'refs/heads/main'", self.config)
        self.assertIn("github.event_name == 'workflow_dispatch'", self.config)

    def test_owner_issue_dispatch_guard_is_preserved(self):
        self.assertIn("github.event.issue.user.login == github.repository_owner", self.config)
        self.assertIn("startsWith(github.event.issue.title, 'oauth-pages:')", self.config)

    def test_pages_deployment_permissions_unchanged(self):
        self.assertIn("  pages: write", self.config)
        self.assertIn("  id-token: write", self.config)


if __name__ == "__main__":
    unittest.main()
