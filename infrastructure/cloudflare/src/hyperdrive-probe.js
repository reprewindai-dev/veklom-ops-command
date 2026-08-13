export default {
  async fetch(request, env) {
    const { Client } = await import("pg");
    const client = new Client({ connectionString: env.HYPERDRIVE_CACHEABLE.connectionString });
    try {
      await client.connect();
      const r = await client.query("SELECT current_database() AS db, current_user AS usr, version() AS ver, now() AS ts;");
      await client.end();
      return Response.json({ ok: true, row: r.rows[0], hyperdrive_host: env.HYPERDRIVE_CACHEABLE.host });
    } catch(e) {
      return Response.json({ ok: false, error: e.message }, { status: 500 });
    }
  }
}
