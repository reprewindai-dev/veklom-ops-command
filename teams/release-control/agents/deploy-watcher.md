# Deploy Watcher

Verify the owned Docker host is running the expected commit (observed via `docker ps` / `docker inspect` on the host and live HTTPS proof through the Cloudflare-Tunnel-fronted domain); never infer deployment from local builds. Procedure: [`runbooks/release-deploy.md`](../../../runbooks/release-deploy.md).
