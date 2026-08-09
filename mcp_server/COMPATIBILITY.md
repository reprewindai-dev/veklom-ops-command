# Veklom Ops MCP Compatibility Note

## Python MCP SDK

This initial implementation intentionally pins:

```text
mcp>=1.27,<2
```

As of August 2026, the upstream Python SDK's v2 line is stable and v1.x is in maintenance mode. The v1.x line continues to receive critical/security fixes, but v2 changes the server implementation and protocol revision.

This is a deliberate rollout choice, not an assumption that v1 is the newest SDK:

1. the current server/App implementation was designed and statically reviewed against the v1.x `FastMCP` APIs;
2. the repository's GitHub Actions runner is presently failing at workflow startup before executing jobs, so the branch does not yet have a clean integration run even on the pinned implementation;
3. changing the MCP protocol/server major in the same security-sensitive PR would combine two independent risk surfaces;
4. ChatGPT's custom-app contract is a remote MCP endpoint/tool contract and does not require this repository to use a particular Python SDK package major.

## Upgrade gate

Migrate to MCP Python SDK v2 in a separate PR after all of the following are true:

- the current MCP package imports and its tests execute in CI or an equivalent trusted runner;
- the hardened container starts successfully;
- ChatGPT Developer Mode can scan the deployed/tunneled endpoint;
- read tools and the Operator Evidence Plane render correctly;
- approval-gated lifecycle tools expose the expected schemas;
- the v2 migration has its own protocol/tool-schema diff review.

The v2 migration must preserve the Veklom invariants rather than merely make imports compile:

- LOW / MEDIUM / HIGH / FORBIDDEN policy behavior;
- public-key-only approval verification in the MCP service;
- exact-parameter/replay protection;
- safe-field projection before output;
- no database writes/arbitrary shell/secret-value reads;
- complete tool authority classification;
- minimal public health surface;
- read/deploy credential separation;
- Apps SDK structured output and widget behavior.

Do not loosen any of those controls to simplify the SDK migration.
