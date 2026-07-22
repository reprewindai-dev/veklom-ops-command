const base = (process.env.VEKLOM_CAPI_URL || '').replace(/\/$/, '');

export function capiConfigured() {
  return Boolean(base);
}

export async function resolveCapability(capability, context = {}) {
  if (!base) return { status: 'not_configured', capability };
  const url = process.env.VEKLOM_CAPI_RESOLVE_URL || `${base}/capabilities/resolve`;
  return postJson(url, { capability, context }, 'cAPI resolve');
}

export async function invokeCapability(capability, input, context = {}) {
  if (!base) throw new Error('cAPI is not configured; capability invocation refused');
  const url = process.env.VEKLOM_CAPI_INVOKE_URL || `${base}/capabilities/invoke`;
  return postJson(url, { capability, input, context }, 'cAPI invoke');
}

function authHeaders() {
  return process.env.VEKLOM_CAPI_TOKEN ? { authorization: `Bearer ${process.env.VEKLOM_CAPI_TOKEN}` } : {};
}

async function postJson(url, body, context) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  const responseText = await response.text();
  let payload;

  try {
    payload = JSON.parse(responseText);
  } catch (error) {
    throw new Error(`${context} returned invalid JSON: ${error.message}`);
  }

  if (!response.ok) {
    if (response.status === 402) {
      const facilitatorUrl = response.headers.get("x-402-facilitator-url") || "Unknown Facilitator";
      console.error(`\n[X402 PAYWALL HIT] ${context} demands payment to proceed.`);
      console.error(`Free tier exhausted. To continue this command, please authorize a payment to:`);
      console.error(`--> ${facilitatorUrl}\n`);
    }
    throw new Error(`${context} failed (${response.status}): ${responseText.slice(0, 400)}`);
  }

  return payload;
}
