import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_live = load_module("verify_live", ROOT / "scripts" / "verify_live.py")
validate_release = load_module("validate_release", ROOT / "scripts" / "validate_release.py")


class JsonResponse:
    def __init__(self, value):
        self.payload = json.dumps(value).encode()

    def __enter__(self):
        import io
        self.stream = io.BytesIO(self.payload)
        return self.stream

    def __exit__(self, *_):
        return False


class WorkflowIntegrationTests(unittest.TestCase):
    def run_script(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *map(str, args)],
            capture_output=True,
            text=True,
        )

    def test_source_update_success_then_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            args = (
                "--source", source, "--app", "kyro", "--version", "9.9.9",
                "--build", "999", "--size", "100", "--tag", "kyro-v9.9.9-b999",
                "--asset", "kyro.ipa",
            )
            first = self.run_script("update_source.py", *args)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_script("update_source.py", *args)
            self.assertNotEqual(second.returncode, 0, "duplicate version/build was accepted")

    def test_source_update_rejects_unknown_app(self):
        result = self.run_script(
            "update_source.py", "--app", "unknown", "--version", "1.0.0",
            "--build", "1", "--size", "1", "--tag", "x", "--asset", "x.ipa",
        )
        self.assertNotEqual(result.returncode, 0, "unknown app was accepted")

    def test_recovery_accepts_exact_release_and_rejects_mismatched_asset(self):
        digest = "a" * 64
        release = {
            "tag_name": "kyro-v1.0.0-b22",
            "draft": False,
            "assets": [{
                "name": "kyro.ipa", "state": "uploaded", "size": 123,
                "digest": f"sha256:{digest}",
                "browser_download_url": "https://example.test/kyro.ipa",
            }],
        }
        url = validate_release.validate_release(
            release, "kyro-v1.0.0-b22", "kyro.ipa", digest, 123
        )
        self.assertEqual(url, "https://example.test/kyro.ipa")
        mismatched = json.loads(json.dumps(release))
        mismatched["assets"][0]["name"] = "different.ipa"
        with self.assertRaisesRegex(ValueError, "asset mismatch"):
            validate_release.validate_release(
                mismatched, "kyro-v1.0.0-b22", "kyro.ipa", digest, 123
            )

    def test_repeated_source_recovery_is_idempotent_and_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "source.json"
            shutil.copy(ROOT / "source.json", source)
            common = (
                "--source", source, "--app", "kyro", "--version", "8.8.8",
                "--build", "888", "--size", "123", "--tag", "kyro-v8.8.8-b888",
                "--asset", "kyro.ipa", "--date", "2026-11-05",
            )
            first = self.run_script("update_source.py", "--idempotent", *common)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = source.read_bytes()
            retry = self.run_script("update_source.py", "--idempotent", *common)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertEqual(source.read_bytes(), before, "retry changed an already exact source entry")
            mismatched = list(common)
            mismatched[mismatched.index("123")] = "124"
            rejected = self.run_script("update_source.py", "--idempotent", *mismatched)
            self.assertNotEqual(rejected.returncode, 0, "mismatched recovery was accepted")

    def test_pages_retry_treats_successful_stale_json_as_failure_then_converges(self):
        expected = {"version": 2}
        responses = iter((JsonResponse({"version": 1}), JsonResponse(expected)))
        sleeps = []
        with mock.patch.object(verify_live.urllib.request, "urlopen", side_effect=lambda *_a, **_k: next(responses)):
            verify_live.verify(expected, "https://example.test/source.json", 2, 0.01, 1, sleeps.append)
        self.assertEqual(sleeps, [0.01])

    def test_pages_retry_fails_after_bound_when_json_stays_stale(self):
        with mock.patch.object(
            verify_live.urllib.request,
            "urlopen",
            side_effect=lambda *_a, **_k: JsonResponse({"version": 1}),
        ):
            with self.assertRaisesRegex(RuntimeError, "after 3 attempts"):
                verify_live.verify({"version": 2}, "https://example.test/source.json", 3, 0, 1, lambda _: None)

    def test_file_verifier_accepts_exact_bytes_and_rejects_wrong_digest_and_size(self):
        with tempfile.NamedTemporaryFile() as handle:
            handle.write(b"candidate ipa bytes")
            handle.flush()
            digest = hashlib.sha256(b"candidate ipa bytes").hexdigest()
            good = self.run_script("verify_file.py", handle.name, "--sha256", digest, "--size", "19")
            self.assertEqual(good.returncode, 0, good.stderr)
            bad_sha = self.run_script("verify_file.py", handle.name, "--sha256", "0" * 64, "--size", "19")
            self.assertNotEqual(bad_sha.returncode, 0, "wrong digest was accepted")
            bad_size = self.run_script("verify_file.py", handle.name, "--sha256", digest, "--size", "18")
            self.assertNotEqual(bad_size.returncode, 0, "wrong size was accepted")

    def test_workflow_has_stage_validate_publish_transitions_and_cross_run_permissions(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-beta.yml").read_text()
        self.assertIn("options: [stage, validate, publish]", workflow)
        self.assertIn("if: inputs.operation == 'stage'", workflow)
        self.assertIn("if: inputs.operation == 'validate' || inputs.operation == 'publish'", workflow)
        self.assertIn("needs: validate", workflow)
        self.assertGreaterEqual(workflow.count("actions: read"), 3)
        self.assertEqual(workflow.count("run-id: ${{ inputs.artifact_run_id }}"), 2)
        self.assertEqual(workflow.count("github-token: ${{ secrets.GITHUB_TOKEN }}"), 2)
        self.assertIn("actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("Create or resume exact public beta release", workflow)
        self.assertIn("matching source-update PR already exists", workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
