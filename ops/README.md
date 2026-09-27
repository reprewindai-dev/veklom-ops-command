# Veklom shared operating contract v1

These four machine files form one contract:

- `veklom-ops.schema.json`: JSON Schema Draft 2020-12 for the shared state.
- `veklom-ops.example.json`: **unverified starter**, with empty evidence and null runtime observations. Replace IDs and values after inventory. Nothing in it is a production seal.
- `validate_ops.py`: cross-record checks JSON Schema cannot express (ownership, WIP, refs, image identity, release gates, and phase order).
- `self_test.py`: negative test battery for validation behavior, including an Anchor false-readiness regression.

`build_schema.py` regenerates the checked-in schema. It writes UTF-8 bytes with LF line endings on Windows and Unix so the same input produces the same schema hash. Commit the generated JSON along with builder changes. Put this directory in the shared repo under `ops/`; keep a single live `ops/veklom-ops.json` copied initially from the example. Do not keep three different agent-owned manifests. Every agent reads the same file and changes only tasks it owns through a task-scoped PR; Codex integrates it. A branch has the shape `work/<task-id-lowercase>/<owner>` and starts at the recorded `base_sha`. If ownership switches, handoff fields must record old/new owner, failing boundary, branch and next action before any edit.

**Allowed deployment surfaces are fixed:** Cloudflare Pages, Cloudflare Tunnel, Docker, and self-owned hardware. Record the actual observed deployment per service; do not assume the frontend is on Pages when it is running as a Docker service. `policy.allowed_surfaces` is locked to these four surfaces; the schema rejects Vercel, Hetzner, Coolify, BYOS, and `veklom-byos-backend` in runtime/release components. There is no alternate cloud-hosted service or BYOS backend in this plan. A canary may be isolated on the same owned hardware if the runtime and secrets are separate.

```sh
python -m pip install 'jsonschema>=4,<5'
python ops/validate_ops.py ops/veklom-ops.json ops/veklom-ops.schema.json
python ops/self_test.py
```

Require both commands in CI before branch integration. Require a protected review on changes to the manifest and schema; CI is a gate on submitted data, not proof that a manually typed log describes reality. Record observation artifacts outside the JSON, and store their SHA-256 plus link in `evidence[]`. Never store credentials, raw customer data, or auth headers.

## External WebMCP reproduction

`verify_external_webmcp.py` is the Phase 8 verifier. It executes one synthetic
governed-counter increment, confirms the readback and PGL reference, checks a
forbidden action has no effect, terminates the successful mount, then replays
the exact successful request and checks the state remains unchanged. It writes
runner/network provenance and a redacted JSON artifact. It does not prove
Stripe/Base settlement, Anchor, or production readiness.

Run only from a separately provisioned machine or hosted runner after reviewing
the target runtime and confirming the synthetic write is approved:

```sh
python ops/verify_external_webmcp.py \
  --runner-provider github-actions \
  --runner-id "$GITHUB_RUN_ID" \
  --source-sha <40-or-64-hex-source-sha> \
  --runtime-ref <exact-runtime-image-digest-or-deployment-id> \
  --veklom-hostname <recorded-container-or-runtime-hostname> \
  --veklom-hardware-hostname <recorded-physical-production-hostname> \
  --veklom-network-cidr <recorded-private-runtime-cidr> \
  --confirm-governed-counter-write
```

For GitHub Actions, the `runner-id` must equal the actual `GITHUB_RUN_ID`; a
caller cannot merely label a local run as GitHub-hosted. The recorded physical
host name is also required so running this from the same machine fails closed.
Do not run this from the Veklom Docker host and do not fill provenance fields
with guesses. If runner provenance or the exact source/runtime reference is
unknown, the external-reproduction claim stays `NOT_PROVED`.

## Agent update contract

1. **Codex:** inventory actual production and canary container IDs, repo commits, image digests, Pages deployment and Tunnel origin into `baseline`. Unknown values stay `null`/`UNKNOWN`, never guesses. Own release candidate integration and the `INTENT → CHANGED → OBSERVED` or `ROLLED_BACK` sequence for production touches.
2. **Antigravity:** claim task-scoped bulk work, isolate concurrency/revocation/lost-response tests, and record actual test artifacts and independent target readback with operation ID. Handoff minimal patch and failing case for Codex review. No production touch.
3. **Devin:** claim frontend or validation tasks, review user journey and public browser trace against the candidate image, point to exact failing request/response, and review agent drift. Devin may correct an owned task through explicit handoff, without silently rewriting another agent's branch.
4. **Anthony:** select the approved customer action, priority override and customer-safe scope. A customer demo may preempt default production work only with `priority_override_reason` and `return_to_work_id` recorded.

## Repository-first portable-work-order contract

Veklom is an existing multi-repository system, not a greenfield build. Before creating or changing a component, map it to its canonical repository and inspect its current implementation. Extend or wire existing components; create a replacement only when explicitly designated `NEW / BUILD`. If a named canonical component cannot be found, report `CANONICAL_COMPONENT_NOT_FOUND` and stop rather than inventing a substitute. GnomLedger / PGL is the evidence system; CAPPO owns consequence authority; LockerPhycer owns authentication/session state; cAPI owns governed connection/discovery; VNP owns observation; ABIDE owns blueprint/contract compilation. No new platform, runtime authority, subsystem, or topology dependency may be added without an architecture decision committed to the canonical source first. “Done” requires repository/runtime proof appropriate to the claim, not generated files or unit tests alone.

## Release interpretation

`CANDIDATE` can carry UNKNOWN gates. `READY` requires recorded healthy canary and required PASS gates with matching component SHA/digests and evidence refs. `PROMOTED` also requires matching production SHAs/digests, production evidence and an `OBSERVED` change. Docker images are addressed by immutable `sha256:...`; the Pages deployment ID and commit are separate artifacts. `latest` and permanent writable `canary-<agent>` branches are intentionally absent: they cannot identify the artifact that was actually tested.

The schema and validator establish consistency of *claims*, not authenticity. A person still has to verify the running container, Pages/Tunnel state, independent target readback and PGL result. If the latter do not exist, the gate is `UNKNOWN` or `BLOCKED`. An Anchor release must include SDK and MCP evidence, plus an actual Anchor session, lost-ack event, and exactly-one independent target readback all marked `anchor_external` and bound to the same operation ID before it can be `READY`. Do not equate Anchor run completion with a committed external effect.

## Production change rule

Write `INTENT` before a Docker, Cloudflare, secret, route, migration or restart change; identify rollback artifacts. After executing, write `CHANGED` with old and new references. Then independently check the public journey and append `OBSERVED`, or append `ROLLED_BACK` and record actual running artifacts. Preserve review history through repository commits; the JSON file alone is mutable and does not supply an append-only audit log.

The example explicitly records separate production inventory, login, payment or entitlement, and fresh-user journey tasks. These are unclaimed assignments and desired outcomes, not claims that the routes or features currently exist.
