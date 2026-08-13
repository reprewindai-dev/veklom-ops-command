# AGENTS.md — READ FIRST

Before any work in Veklom Ops Command, read [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md).

Then read [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md), [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md), and [`AGENT_MANIFEST.md`](./AGENT_MANIFEST.md).

The Bible is the sole cross-repo architecture/runtime/topology/port authority. Do not copy infrastructure constants into agent prompts or role files. Use Coolify UI/API/MCP for Coolify management; reserve SSH for direct host/container verification or operations. Host `8000` is currently Coolify-owned; internal Docker `8000` may still be used behind Traefik.

## Security & Architecture Enforcement
- **Cloudflare & Web Bot Auth**: Cloudflare serves as the perimeter for identity verification. Agents must strictly adhere to the Web Bot Auth requirements (Ed25519 keys, `.well-known` signed JWKS).
- **CAPPO Authority**: Web Bot Auth proves identity, not capability. CAPPO retains exclusive authority over consequential execution, mount validity, and token generation. Agents must never bypass CAPPO for capability grants.
- **cAPI Separation**: cAPI acts as a proxy for verified identity and must never synthesize grants. Never alias `CAPPO_BACKEND_URL` to `CAPI_RUNTIME_URL`.
