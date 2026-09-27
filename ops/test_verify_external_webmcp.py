import importlib.util
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("verify_external_webmcp.py")
SPEC = importlib.util.spec_from_file_location("verify_external_webmcp", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class ExternalVerifierHelpersTest(unittest.TestCase):
    def test_mount_extracts_mount_id_not_unrelated_nested_id(self):
        payload = {
            "decision": "allow",
            "workspace": {"id": "workspace-1"},
            "mount": {"id": "mnt_123"},
            "token": {"token_id": "tok_456", "nonce": "n_789"},
        }
        self.assertEqual(
            verifier.extract_mount_fields(payload),
            ("mnt_123", "tok_456", "n_789"),
        )

    def test_mount_supports_flat_fields_but_rejects_ambiguous_id(self):
        flat = {"mount_id": "mnt_1", "token_id": "tok_2", "nonce": "n_3"}
        self.assertEqual(verifier.extract_mount_fields(flat), ("mnt_1", "tok_2", "n_3"))
        with self.assertRaisesRegex(RuntimeError, "did not expose"):
            verifier.extract_mount_fields({"id": "workspace-1", "token": {"nonce": "n"}})

    def test_evidence_verification_argument_comes_from_field_name(self):
        self.assertEqual(
            verifier.extract_evidence_reference({"result": {"event_hash": "rcpt_not_a_hash"}}),
            ("event_hash", "rcpt_not_a_hash"),
        )
        self.assertEqual(
            verifier.extract_evidence_reference({"receipt_id": "sha256:looks-like-a-hash"}),
            ("receipt_id", "sha256:looks-like-a-hash"),
        )

    def test_evidence_verification_accepts_nested_confirmation(self):
        self.assertTrue(verifier.evidence_verification_succeeded({"verification": {"verified": True}}))
        self.assertTrue(verifier.evidence_verification_succeeded({"ledger": {"status": "confirmed"}}))
        self.assertFalse(verifier.evidence_verification_succeeded({"verified": False, "status": "denied"}))

    def test_exact_replay_digest_is_deterministic_and_redaction_is_recursive(self):
        args = verifier.build_action_arguments("mnt_1", "tok_2", "n_3", "counter.increment", "ws_4")
        self.assertEqual(verifier.canonical_hash(args), verifier.canonical_hash(dict(reversed(list(args.items())))))
        self.assertEqual(verifier.redact({"token_id": "tok", "nested": {"nonce": "n"}}), {
            "token_id": "[REDACTED]",
            "nested": {"nonce": "[REDACTED]"},
        })

    def test_offline_lifecycle_fixture_checks_exact_replay_without_network(self):
        class FakeMCP:
            def __init__(self, _base_url, report):
                self.report = report
                self.mount_number = 0
                self.mounts = {}
                self.state = 0

            def rpc(self, method, params=None):
                if method == "tools/list":
                    return {"result": {"tools": [{"name": name} for name in sorted(verifier.CONSEQUENCE_TOOLS | {"veklom_discover_capabilities"})]}}
                raise AssertionError(f"unexpected RPC method: {method}")

            def request_json(self, _url, method="GET", body=None):
                return {"tools": [{"name": name} for name in sorted(verifier.CONSEQUENCE_TOOLS | {"veklom_discover_capabilities"})]}

            def call_tool(self, name, arguments):
                if name == "veklom_discover_capabilities":
                    return {"capabilities": [{"package_ref": verifier.PACKAGE_REF}]}
                if name == "veklom_mount_capability":
                    self.mount_number += 1
                    mount_id = f"mnt_{self.mount_number}"
                    self.mounts[mount_id] = {"terminated": False, "workspace": arguments["workspace"]}
                    return {"decision": "allow", "mount": {"id": mount_id}, "token": {"token_id": f"tok_{self.mount_number}", "nonce": f"nonce_{self.mount_number}"}}
                if name == "veklom_read_target_state":
                    return {"state": {"value": self.state}}
                if name == "veklom_execute_action":
                    mount = self.mounts[arguments["mount_id"]]
                    if mount["terminated"] or arguments["action"] == "counter.reset":
                        return {"decision": "deny", "reason": "inactive_or_blocked"}
                    if arguments["action"] == "counter.increment" and self.state == 0:
                        self.state += 1
                        return {"decision": "allow", "consequence": {"receipt_id": "rcpt_fixture"}}
                    return {"decision": "deny", "reason": "already_used"}
                if name == "veklom_verify_evidence":
                    self.assert_evidence_reference = arguments
                    return {"verified": True, "status": "confirmed"}
                if name == "veklom_terminate_mount":
                    self.mounts[arguments["mount_id"]]["terminated"] = True
                    return {"decision": "allow"}
                raise AssertionError(f"unexpected tool: {name}")

        args = SimpleNamespace(base_url="https://example.invalid")
        report = {"checks": [], "http_trace": []}
        with patch.object(verifier, "discover_target", return_value=(["203.0.113.9"], ["example.invalid"])), \
             patch.object(verifier, "PublicMCP", FakeMCP):
            verifier.verify(args, report)

        self.assertGreaterEqual(len(report["checks"]), 12)
        self.assertTrue(all(check["result"] == "PASS" for check in report["checks"]))
        self.assertEqual(report["evidence_reference"], "rcpt_fixture")
        replay_check = next(check for check in report["checks"] if check["name"] == "exact action replay after termination denied")
        self.assertEqual(replay_check["observed"], "deny")

    def test_github_actions_provenance_must_match_the_actual_runner_environment(self):
        args = SimpleNamespace(
            runner_provider="github-actions",
            runner_id="run-123",
            veklom_hostname=["veklom-container"],
            veklom_hardware_hostname="veklom-host",
            veklom_network_cidr=["172.19.0.0/16"],
        )
        with patch.object(verifier, "local_addresses", return_value=["192.0.2.5"]), \
             patch("socket.gethostname", return_value="hosted-runner"), \
             patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "run-123", "GITHUB_REPOSITORY": "owner/repo"}, clear=True):
            verified = verifier.provenance(args)
        self.assertTrue(verified["eligible_as_independent_runner"])
        self.assertEqual(verified["github_run_id"], "run-123")

        with patch.object(verifier, "local_addresses", return_value=["192.0.2.5"]), \
             patch("socket.gethostname", return_value="hosted-runner"), \
             patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}, clear=True):
            falsely_labeled = verifier.provenance(args)
        self.assertFalse(falsely_labeled["eligible_as_independent_runner"])

    def test_exact_source_and_runtime_refs_reject_placeholders(self):
        self.assertEqual(verifier.source_sha_argument("a" * 40), "a" * 40)
        with self.assertRaises(Exception):
            verifier.source_sha_argument("not-a-sha")
        with self.assertRaises(Exception):
            verifier.runtime_ref_argument("latest")


if __name__ == "__main__":
    unittest.main()
