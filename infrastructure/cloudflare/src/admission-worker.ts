/**
 * VEKLOM Edge Admission Worker
 *
 * Runs at the NEAREST Cloudflare PoP to the incoming request (default, no placement config).
 * Cloudflare AI Crawl Control + WAF rules handle primary crawler classification BEFORE
 * this worker runs. This worker handles what Cloudflare classification doesn't decide:
 * - Route classification
 * - MCP protocol detection
 * - x402 prerequisite for monetized resources
 * - Auth prerequisite check (soft gate — hard auth is CAPPO's job)
 * - Quota / rate early refusal
 * - Obvious rejection
 *
 * IMPORTANT: We rely on cf.client.bot (available on all plans), NOT cf.botManagement.*
 * which requires Enterprise Bot Management. Corporate proxy != trusted; don't auto-admit
 * corporate proxy traffic.
 *
 * The Worker communicates to the Origin-Near Connector via Service Binding (no public hop).
 */

export interface Env {
  VEKLOM_IMMUTABLE_CACHE: KVNamespace;
  REFINERY_QUEUE: Queue;
  ORIGIN_CONNECTOR: Fetcher; // Service Binding to veklom-origin-connector
}

// Surfaces the application enforces regardless of crawler status.
// Cloudflare = who may approach the door.
// Application/CAPPO = who may enter.
const DENY_SURFACE = [
  '/os',
  '/admin',
  '/api/private',
  '/evidence/private',
  '/internal',
];

// Routes that require MCP auth + payment/governance requirements
const MCP_SURFACE = ['/mcp'];

// Public search surface — free for legitimate search bots
const SEARCH_SURFACE = [
  '/',
  '/about',
  '/pricing',
  '/docs',
  '/blog',
  '/sitemap.xml',
  '/robots.txt',
  '/.well-known',
];

function isOnSurface(pathname: string, surfaces: string[]): boolean {
  return surfaces.some(s => pathname === s || pathname.startsWith(s + '/'));
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const cf = (request as any).cf || {};

    // ── Level 0: cf.client.bot (all plans) ──────────────────────────────────
    // cf.client.bot is a structured object when Cloudflare detects a known bot.
    // cf.verified_bot_category differentiates search engines from AI crawlers
    // where available. Primary classification lives in Cloudflare AI Crawl Control
    // and WAF rules — this is secondary enforcement.
    const isVerifiedBot = cf.verified_bot === true || cf.bot_management?.verified_bot === true;
    const botCategory: string = cf.bot_management?.ja4 ?? cf.verified_bot_category ?? '';
    // Threat score: 0 = trusted, 100 = malicious. Available all plans.
    const threatScore: number = typeof cf.threat_score === 'number' ? cf.threat_score : 0;

    // ── Level 1: Block clearly malicious traffic ─────────────────────────────
    // High threat score and not a verified bot = drop early.
    if (threatScore > 70 && !isVerifiedBot) {
      return new Response(null, { status: 403 });
    }

    // ── Level 2: MCP surface — requires auth + optional x402 ────────────────
    if (isOnSurface(path, MCP_SURFACE)) {
      const authHeader = request.headers.get('Authorization');
      const mcpVersion = request.headers.get('MCP-Version');

      // MCP requests must present a bearer token (hard auth lives in CAPPO)
      if (!authHeader?.startsWith('Bearer ')) {
        return new Response(
          JSON.stringify({ error: 'mcp_auth_required', message: 'MCP surface requires Bearer authentication.' }),
          { status: 401, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // x402: If a paid MCP resource header is present, validate payment header exists
      const x402Required = request.headers.get('X-Veklom-x402-Required');
      if (x402Required === 'true' && !request.headers.get('Payment-Signature')) {
        return new Response(
          JSON.stringify({
            error: 'payment_required',
            message: 'This MCP capability requires x402 settlement.',
            headers: {
              'Payment-Required': 'true',
              'Payment-Schema': 'x402-v2',
            }
          }),
          { status: 402, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // ── Level 3: DENY_SURFACE requires auth token to be present (soft gate) ─
    // Hard authorization is CAPPO's job. We only check presence here.
    if (isOnSurface(path, DENY_SURFACE)) {
      const authHeader = request.headers.get('Authorization');
      if (!authHeader) {
        return new Response(
          JSON.stringify({ error: 'authentication_required' }),
          { status: 401, headers: { 'Content-Type': 'application/json', 'WWW-Authenticate': 'Bearer' } }
        );
      }
    }

    // ── Level 4: Verified bots are confined to SEARCH_SURFACE ───────────────
    // AI Crawl Control blocks AI training bots before reaching here.
    // This catches any verified search bot trying to wander into governed surfaces.
    if (isVerifiedBot && !isOnSurface(path, SEARCH_SURFACE)) {
      return new Response(null, { status: 403 });
    }

    // ── Forward to Origin-Near Connector via Service Binding ─────────────────
    // Service Bindings are zero-cost (no extra billed request) and stay
    // within Cloudflare's private network — no public endpoint exposed.
    return env.ORIGIN_CONNECTOR.fetch(request);
  },
};
