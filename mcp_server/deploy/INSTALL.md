# Veklom Gate — install in about five minutes

Veklom Gate lets an AI agent (Claude Code, Cursor, ChatGPT…) read and operate the Docker containers you choose, on your own server, without ever holding the Docker socket. It starts **read-only**; actions are switched on deliberately in step 5.

You need: a Linux host with Docker Compose v2, and a hostname for the MCP endpoint (a Cloudflare Tunnel is the easiest way to get one without opening a port).

## 1. Get the files

```bash
mkdir veklom-gate && cd veklom-gate
curl -fsSLO https://raw.githubusercontent.com/reprewindai-dev/veklom-ops-command/main/mcp_server/deploy/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/reprewindai-dev/veklom-ops-command/main/mcp_server/deploy/cloudflare-tunnel.yml
```

## 2. Generate secrets

```bash
docker run --rm -v "$PWD:/out" -w /out ghcr.io/reprewindai-dev/veklom-gate:latest \
  veklom-gate-init \
    --audience acme-prod \
    --public-url https://ops.example.com \
    --approver-url https://approve.example.com/ \
    --socket-gid "$(stat -c %g /var/run/docker.sock)"
```

This writes `.env` with three fresh random tokens, read-only switches, and `chmod 600`. Use your own names: `--audience` is what every approval is bound to, so give each server a different one.

## 3. Choose what the agent may see

Only containers with this label exist as far as the agent is concerned:

```yaml
services:
  web:
    labels:
      veklom.ops.managed: "true"
    healthcheck:                       # needed for restarts without a human
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    deploy:
      replicas: 2                      # two healthy copies => restarts are autonomous
```

Leave databases unlabelled unless you want the agent to read their logs.

## 4. Start it

```bash
# With a Cloudflare Tunnel (put the tunnel token in CLOUDFLARE_TUNNEL_TOKEN in .env and point
# the tunnel's public hostname at http://veklom-ops-mcp:8787):
docker compose -f docker-compose.yml -f cloudflare-tunnel.yml up -d

# Without one (bring your own reverse proxy onto the compose network):
docker compose up -d
```

Connect your agent, using `VEKLOM_MCP_ACCESS_TOKEN` from `.env`. For Claude Code:

```bash
claude mcp add --transport http veklom-gate https://ops.example.com/mcp \
  --header "Authorization: Bearer <VEKLOM_MCP_ACCESS_TOKEN>"
```

Ask it: *"List my managed containers and show me the last 50 log lines of the web service."* Unlabelled containers will not appear, and env values never will.

## 5. Turn on actions, with your phone as the key

1. Host the approver page on its **own** origin (never on the MCP host name). With Cloudflare Pages:
   ```bash
   npx wrangler pages deploy approver --project-name veklom-gate-approver
   ```
   (`approver/` is in the repo at `mcp_server/approver/`; `_headers` sets its security headers.)
2. Open it on your phone, enter your name, tap **Create signing key**. The key is generated in the phone's browser and cannot be exported.
3. Copy the env line it shows into `.env`, and flip both switches:
   ```text
   VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64=<from the approver page>
   VEKLOM_MCP_WRITES_ENABLED=true
   DOCKER_GATE_ALLOW_ACT=true
   ```
4. `docker compose up -d` again.

Now ask the agent to restart one replica of a healthy two-replica service: it just does it. Ask it to stop something: it replies with a link. Open it on your phone, check exactly what will run, hold **Approve once**, and the agent's retry goes through — once.

## What to check before trusting it

- `list_containers` shows only labelled containers.
- `get_container_env_presence` shows names, never values.
- A stop without approval returns `approval_required`; the same approval cannot be used twice.
- `docker compose ps`: only `docker-gate` mounts `/var/run/docker.sock`, and nothing publishes a port.

Read `../SECURITY.md` for the threat model, including what happens if the gate itself is compromised.
