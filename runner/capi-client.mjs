const base = (process.env.VEKLOM_CAPI_URL || '').replace(/\/$/, '');

export function capiConfigured() { return Boolean(base); }

export async function resolveCapability(capability, context = {}) {
  if (!base) return { status: 'not_configured', capability };
  const url = process.env.VEKLOM_CAPI_RESOLVE_URL || `${base}/capabilities/resolve`;
  const response = await fetch(url, {method:'POST', headers:{'content-type':'application/json', ...authHeaders()}, body:JSON.stringify({capability, context})});
  const payload = await response.json();
  if (!response.ok) throw new Error(`cAPI resolve failed (${response.status})`);
  return payload;
}

export async function invokeCapability(capability, input, context = {}) {
  if (!base) throw new Error('cAPI is not configured; capability invocation refused');
  const url = process.env.VEKLOM_CAPI_INVOKE_URL || `${base}/capabilities/invoke`;
  const response = await fetch(url, {method:'POST', headers:{'content-type':'application/json', ...authHeaders()}, body:JSON.stringify({capability, input, context})});
  const payload = await response.json();
  if (!response.ok) throw new Error(`cAPI invoke failed (${response.status})`);
  return payload;
}

function authHeaders() { return process.env.VEKLOM_CAPI_TOKEN ? {'authorization':`Bearer ${process.env.VEKLOM_CAPI_TOKEN}`} : {}; }
