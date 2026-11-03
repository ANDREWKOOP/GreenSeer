import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "audit_public_package.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_public_package", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PublicPackageAuditTests(unittest.TestCase):
    def setUp(self):
        self.module = load_audit_module()

    def audit_fixture(self, files, max_bytes=50_000_000):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            root = Path(temp_dir)
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
            return self.module.audit_tree(root, max_bytes=max_bytes)

    def test_rejects_private_paths_tenant_urls_and_credentials(self):
        findings = self.audit_fixture(
            {
                "local.md": r"Built at C:\Users\max\project",
                "tenant.html": "https://hack-example.engage.sas.com/SASVisualAnalytics/",
                "secret.txt": "api_key = sk-example-secret-value",
            }
        )
        rules = {finding.rule for finding in findings}
        self.assertIn("local-path", rules)
        self.assertIn("sas-tenant", rules)
        self.assertIn("credential", rules)

    def test_rejects_archives_internal_directories_and_large_files(self):
        findings = self.audit_fixture(
            {
                "bundle.zip": b"PK",
                ".agents/SKILL.md": "private instructions",
                "too-large.mp4": b"x" * 101,
            },
            max_bytes=100,
        )
        rules = {finding.rule for finding in findings}
        self.assertIn("archive", rules)
        self.assertIn("internal-directory", rules)
        self.assertIn("file-size", rules)

    def test_accepts_expected_public_file_types_below_limit(self):
        findings = self.audit_fixture(
            {
                "index.html": "<main>GreenSeer</main>",
                "data/project.json": '{"project": "GreenSeer"}',
                "data/sample.csv": "date,value\n2020-01-01,1\n",
                "assets/chart.png": b"PNG",
                "README.md": "# GreenSeer",
                "src/router.py": "def route(): return 'review'\n",
                "media/pitch.mp4": b"MP4",
            }
        )
        self.assertEqual([], findings)

    def test_release_scan_ignores_auditor_rules_and_test_fixtures(self):
        findings = self.audit_fixture(
            {
                "scripts/audit_public_package.py": r"RULE = 'C:\\Users\\'",
                "tests/test_public_audit.py": "api_key = sk-example-fixture",
                "docs/index.html": "<main>GreenSeer</main>",
            }
        )
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
