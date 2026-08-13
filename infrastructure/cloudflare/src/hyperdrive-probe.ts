/**
 * Hyperdrive Probe — temp verification worker.
 * Wraps all errors to JSON so nothing is silently swallowed.
 */
import { Client } from "pg";

interface Env {
  HYPERDRIVE_CACHEABLE: Hyperdrive;
  HYPERDRIVE_FRESH: Hyperdrive;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== "/probe") {
      return new Response("not found", { status: 404 });
    }

    const out: Record<string, unknown> = {
      ts: new Date().toISOString(),
      hd_host: env.HYPERDRIVE_CACHEABLE.host,
      hd_port: env.HYPERDRIVE_CACHEABLE.port,
      hd_db: env.HYPERDRIVE_CACHEABLE.database,
      hd_user: env.HYPERDRIVE_CACHEABLE.user,
      conn_string_prefix: env.HYPERDRIVE_CACHEABLE.connectionString.slice(0, 30) + "…",
    };

    // --- Test cacheable ---
    try {
      const c = new Client({ connectionString: env.HYPERDRIVE_CACHEABLE.connectionString });
      await c.connect();
      const r = await c.query("SELECT current_database() db, current_user usr, now() ts;");
      await c.end();
      out.cacheable = { ok: true, db: r.rows[0].db, user: r.rows[0].usr, server_ts: r.rows[0].ts };
    } catch (e: unknown) {
      out.cacheable = { ok: false, error: String(e) };
    }

    // --- Test fresh ---
    try {
      const c2 = new Client({ connectionString: env.HYPERDRIVE_FRESH.connectionString });
      await c2.connect();
      const r2 = await c2.query("SELECT COUNT(*)::int cnt FROM information_schema.tables WHERE table_schema='public';");
      await c2.end();
      out.fresh = { ok: true, public_tables: r2.rows[0].cnt };
    } catch (e: unknown) {
      out.fresh = { ok: false, error: String(e) };
    }

    return Response.json(out, { headers: { "X-Veklom-Probe": "hd-v2", "Cache-Control": "no-store" } });
  },
};
