import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "verify_public_release.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_public_release", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseVerifierTests(unittest.TestCase):
    def test_current_repository_passes_non_test_checks(self):
        report = load_verifier().verify_release(ROOT, run_tests=False)
        self.assertTrue(report.passed, report)
        self.assertEqual(0, report.audit_findings)
        self.assertEqual(0, report.broken_links)
        self.assertEqual(0, report.invalid_json)
        self.assertEqual(0, report.source_issues)

    def test_broken_local_link_is_reported(self):
        module = load_verifier()
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")
            report = module.verify_release(root, run_tests=False)
            self.assertFalse(report.passed)
            self.assertEqual(1, report.broken_links)


if __name__ == "__main__":
    unittest.main()
