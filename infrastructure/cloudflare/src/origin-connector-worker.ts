/**
 * VEKLOM Origin-Near Connector Worker
 *
 * Receives requests via Service Binding from the Edge Admission Worker —
 * no public endpoint, no extra billed Cloudflare request.
 *
 * ARCHITECTURE INVARIANT (hard rule):
 *   Cloudflare may classify, reject, route, cache, and transport.
 *   CAPPO alone may authorize execution.
 *
 * This Worker is a TRANSPORT OPTIMIZATION LAYER, not a governance kernel.
 * It may:
 *   - Pool Postgres connections via Hyperdrive (CACHEABLE binding only)
 *   - Proxy requests to CAPPO over the private network path (Tunnel → Server 0)
 *
 * This Worker MUST NOT:
 *   - Read authority, revocations, delegation, permissions, budget, nonce,
 *     LAW 0 state, execution identity, or governance decisions from the DB.
 *   - Say "you're authorized" based on any DB read here.
 *   - Reproduce any CAPPO authorization logic.
 *
 * HYPERDRIVE_CACHEABLE — the ONLY Hyperdrive binding this Worker uses.
 * Reserved for: public capability catalogs, derived Gold statistics,
 * historical aggregates, non-authoritative metadata.
 *
 * HYPERDRIVE_FRESH — declared in wrangler-connector.toml and reserved for
 * future non-authoritative fresh data reads only (e.g., real-time pricing
 * discovery that is NOT an authorization decision). NEVER used for governance.
 *
 * Authoritative governance reads (authority, revocations, budget, LAW 0):
 *   CAPPO → its local/private PostgreSQL → LAW 0 decision.
 * That path is faster anyway — CAPPO and its DB are already co-located.
 * Routing CAPPO's own queries through Worker → Hyperdrive → VPC → Tunnel
 * would add needless latency and create a dangerous second governance path.
 *
 * Placement:
 *   No placement configuration for Phase 4. Smart Placement needs traffic
 *   data to learn. Host-based placement conflicts with the origin-protection
 *   goal (Hetzner origin must not be publicly reachable for TCP probes).
 *   Measure first; optimize later if multiple sequential queries warrant it.
 *
 * Private DB access path (Phase 5, when implemented):
 *   Worker → Hyperdrive → Workers VPC Service → Cloudflare Tunnel → Postgres
 */

export interface Env {
  // Caching ON (60s TTL) — public catalogs, Gold stats, historical aggregates
  // SAFE non-authoritative data ONLY. Never governance state.
  HYPERDRIVE_CACHEABLE: Hyperdrive;
  // Caching DISABLED — reserved for future non-authoritative fresh data.
  // NOT for governance reads. NOT for authority or authorization.
  HYPERDRIVE_FRESH: Hyperdrive;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // This Worker uses HYPERDRIVE_CACHEABLE for the small set of safe,
    // non-authoritative queries (catalog, stats). All other requests are
    // proxied to CAPPO, which uses its co-located DB for governance decisions.
    //
    // Phase 5 will add concrete Hyperdrive query patterns for capability
    // catalog acceleration. Until then, all requests proxy to CAPPO origin.

    const originUrl = new URL(request.url);

    // Allowed origin routes according to the Golden Bible
    const allowedHosts = new Set([
      'apex.veklom.com',
      'bingo.veklom.com',
      'capi.veklom.com',
      'cappo.veklom.com',
      'discovery.veklom.com',
      'duel.veklom.com',
      'id.veklom.com',
      'interlink.veklom.com',
      'ledger.veklom.com',
      'lockerphycer.veklom.com',
      'pgl.veklom.com',
      'repogate.veklom.com',
      'api.veklom.com',
      'control.veklom.com',
      'app.veklom.com',
    ]);

    if (!allowedHosts.has(originUrl.hostname)) {
      return new Response("Unknown backend route", { status: 404 });
    }
    // No default backend fallback; hostname remains the explicitly allowed requested host
    // which Traefik on Server 0 will route.
    // Attach internal connector identity header so CAPPO can verify
    // the request arrived through the private path (for audit + rate-limiting)
    const modifiedHeaders = new Headers(request.headers);
    modifiedHeaders.set('X-Veklom-Connector', 'origin-near-v1');

    const modifiedRequest = new Request(originUrl.toString(), {
      method: request.method,
      headers: modifiedHeaders,
      body: request.body,
    });

    return fetch(modifiedRequest);
  },
};
