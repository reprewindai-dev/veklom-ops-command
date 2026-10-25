// Cryptographic utilities matching Veklom Gate Approver specification

const enc = new TextEncoder();
const dec = new TextDecoder();

export function b64url(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlToText(value: string): string {
  const b64 = value.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((value.length + 3) % 4);
  const bin = atob(b64);
  return dec.decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

export function hex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Canonical JSON serializer matching Python json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)
export function canonical(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) throw new Error("Only integer numbers can be fingerprinted identically.");
    return String(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (typeof value === "object") {
    const keys = Object.keys(value as Record<string, unknown>).sort((a, b) => {
      const x = Array.from(a), y = Array.from(b);
      for (let i = 0; i < Math.min(x.length, y.length); i++) {
        const d = (x[i].codePointAt(0) ?? 0) - (y[i].codePointAt(0) ?? 0);
        if (d) return d;
      }
      return x.length - y.length;
    });
    return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonical((value as Record<string, unknown>)[k])).join(",") + "}";
  }
  throw new Error("Unsupported value in parameters.");
}

export async function sha256hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return hex(digest);
}

export async function computeParamsHash(params: Record<string, unknown>): Promise<string> {
  const canonicalStr = canonical(params);
  return sha256hex(canonicalStr);
}

export function shortHash(hash: string): string {
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 8)}…${hash.slice(-6)}`;
}

// Key Storage in IndexedDB
const DB_NAME = "veklom-gate-approver";
const STORE_NAME = "keys";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE_NAME);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idb<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequest): Promise<T> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, mode);
    const req = fn(tx.objectStore(STORE_NAME));
    tx.oncomplete = () => resolve(req?.result);
    tx.onerror = () => reject(tx.error);
  });
}

export async function isEd25519Supported(): Promise<boolean> {
  try {
    if (!window.crypto?.subtle) return false;
    await crypto.subtle.generateKey({ name: "Ed25519" }, false, ["sign", "verify"]);
    return true;
  } catch {
    return false;
  }
}

export interface StoredKeyRecord {
  privateKey: CryptoKey;
  publicKey: CryptoKey;
  publicB64: string;
  fingerprint: string;
  createdAt: number;
  algorithm: string;
}

export async function loadSigningKey(): Promise<StoredKeyRecord | null> {
  try {
    return await idb<StoredKeyRecord | null>("readonly", (s) => s.get("signing-key"));
  } catch {
    return null;
  }
}

export async function deleteSigningKey(): Promise<void> {
  try {
    await idb("readwrite", (s) => s.delete("signing-key"));
  } catch {
    // ignore
  }
}

export async function generateSigningKey(): Promise<StoredKeyRecord> {
  const edSupported = await isEd25519Supported();
  
  if (edSupported) {
    const pair = (await crypto.subtle.generateKey({ name: "Ed25519" }, false, ["sign", "verify"])) as CryptoKeyPair;
    const raw = new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey));
    const publicB64 = b64url(raw);
    const fingerprint = (await sha256hex(publicB64)).slice(0, 16);
    const record: StoredKeyRecord = {
      privateKey: pair.privateKey,
      publicKey: pair.publicKey,
      publicB64,
      fingerprint,
      createdAt: Date.now(),
      algorithm: "Ed25519"
    };
    await idb("readwrite", (s) => s.put(record, "signing-key"));
    return record;
  } else {
    // ECDSA fallback for runtimes where Ed25519 is restricted
    const pair = (await crypto.subtle.generateKey(
      { name: "ECDSA", namedCurve: "P-256" },
      false,
      ["sign", "verify"]
    )) as CryptoKeyPair;
    const raw = new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey));
    const publicB64 = b64url(raw);
    const fingerprint = (await sha256hex(publicB64)).slice(0, 16);
    const record: StoredKeyRecord = {
      privateKey: pair.privateKey,
      publicKey: pair.publicKey,
      publicB64,
      fingerprint,
      createdAt: Date.now(),
      algorithm: "ECDSA-P256"
    };
    await idb("readwrite", (s) => s.put(record, "signing-key"));
    return record;
  }
}

export async function signApproval(
  key: StoredKeyRecord,
  approver: string,
  req: {
    aud: string;
    tool: string;
    action: string;
    params_sha256: string;
  },
  ttlSeconds: number
): Promise<{ token: string; claims: Record<string, unknown> }> {
  const now = Math.floor(Date.now() / 1000);
  const nonceBytes = new Uint8Array(18);
  crypto.getRandomValues(nonceBytes);

  const claims = {
    v: 2,
    nonce: b64url(nonceBytes),
    aud: req.aud,
    tool: req.tool,
    action: req.action,
    params_sha256: req.params_sha256,
    approved_by: approver,
    issued_at: now,
    expires_at: now + ttlSeconds,
  };

  const payload = enc.encode(JSON.stringify(claims));
  const signAlgorithm = key.algorithm === "Ed25519" ? { name: "Ed25519" } : { name: "ECDSA", hash: { name: "SHA-256" } };
  const signature = new Uint8Array(await crypto.subtle.sign(signAlgorithm, key.privateKey, payload));
  
  return {
    token: `v2.${b64url(payload)}.${b64url(signature)}`,
    claims,
  };
}
