# Release Deploy — Owned Docker Hosts

Current Core V1 runtime is owned/local hardware + Docker + Cloudflare Tunnels ([`CURRENT_ARCHITECTURE_LOCK.md`](../CURRENT_ARCHITECTURE_LOCK.md)). This runbook replaces the retired `runbooks/coolify-deploy.md`.

Release Manager verifies the GitHub commit, the target owned Docker host and compose project, the build result, and the deployment result. No watcher auto-deploys. After deployment, SRE runs HTTPS health, protocol, dependency, and introspect checks.

## Facts that must come from fresh observation

For every service, the following are `UNVERIFIED` in this repository and must be observed on the owned host at deploy time, then recorded in the release proof:

- which owned host runs the service, and the operator-approved access path to it;
- the compose project / directory, container names, and internal ports;
- the Cloudflare Tunnel and public-hostname → service mapping;
- how deployment secrets are injected.

Useful read-only observations: `docker compose ls`, `docker ps`, `docker inspect <container>`, `cloudflared tunnel list`, `cloudflared tunnel info <tunnel>`.

Never reuse Coolify-era paths (`/data/coolify/...`), Hetzner addresses, `deploy_all.sh`, or Coolify/Traefik proxy configuration as a deploy target or as runtime truth.

## Procedure

1. **Source** — reviewed SHA on GitHub `main`, CI green, required sign-offs present, no security hold.
2. **Deploy** — on the observed owned Docker host, bring the service's compose project to the reviewed SHA and run `docker compose up -d --build` (or the equivalent defined by the service repository's compose file).
3. **Runtime proof** — confirm the running container is up and built from the reviewed SHA (`docker ps`, `docker inspect`).
4. **Public proof** — HTTPS health, protocol, dependency, and introspect checks through the Cloudflare-Tunnel-fronted public domain. Unknown or unreachable is not a pass.
5. **Record** — repo, branch, SHA, host (as observed), build, tests, deploy result, live proof, and rollback point.

## Rollback

Redeploy the previous known-good SHA by the same procedure and repeat steps 3–5.

Anything not observed during this release is reported as `UNVERIFIED`.
