from veklom_ops_mcp.redaction import REDACTED, redact, redact_text


def test_recursive_sensitive_keys_are_redacted():
    value = {
        "name": "service",
        "password": "do-not-return",
        "nested": {
            "api_key": "secret-key",
            "safe": "ok",
        },
    }
    output = redact(value)
    assert output["name"] == "service"
    assert output["password"] == REDACTED
    assert output["nested"]["api_key"] == REDACTED
    assert output["nested"]["safe"] == "ok"


def test_bearer_and_env_secret_are_redacted_from_logs():
    text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz TOKEN=supersecret status=ok"
    output = redact_text(text)
    assert "abcdefghijklmnopqrstuvwxyz" not in output
    assert "supersecret" not in output
    assert "status=ok" in output


def test_uri_password_is_redacted():
    output = redact_text("postgres://alice:verysecret@db.internal:5432/app")
    assert "verysecret" not in output
    assert REDACTED in output


def test_output_is_capped():
    output = redact_text("x" * 100, max_chars=20)
    assert output.startswith("x" * 20)
    assert "TRUNCATED" in output
