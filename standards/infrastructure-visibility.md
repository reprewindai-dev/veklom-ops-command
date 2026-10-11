# Infrastructure Visibility Rule

Private operations matrices may contain Docker resource names, Cloudflare Tunnel mappings, internal mappings, and operator-only deployment details.

Public `/protocol.json` manifests must never expose container names, private IPs, secrets, SSH paths, environment variables, internal ports, or raw infrastructure details. Public manifests expose only the approved service contract, capabilities, health links, and safe HTTPS URLs.
