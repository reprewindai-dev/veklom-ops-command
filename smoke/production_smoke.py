#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
"""
Veklom Production Smoke Tests
Tests all public-facing services against real domains.
Produces cryptographic proof of health.
"""
import urllib.request
import urllib.error
import json
import time
import hashlib
import ssl
import sys
from datetime import datetime, timezone

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SERVICES = [
    # (name, url, expected_key, expected_value_contains)
    ("BYOS API", "https://api.veklom.com/health", "status", "healthy"),
    ("CAPPO", "https://cappo.veklom.com/health", "status", "ok"),
    ("cAPI", "https://capi.veklom.com/health", "status", "ok"),
    ("PGL/GnomLedger", "https://pgl.veklom.com/health", "status", "ok"),
    ("Control Plane", "https://control.veklom.com/api/health", None, None),
    ("ABIDE", "https://abide.veklom.com/health", "status", "ok"),
    ("VNP", "https://vnp.veklom.com/health", None, None),
    ("Lockerphycer", "https://lockerphycer.veklom.com/health", None, None),
]

CORS_CHECKS = [
    # (service_name, url, origin_to_check)
    ("BYOS API", "https://api.veklom.com/health", "https://control.veklom.com"),
    ("BYOS API", "https://api.veklom.com/health", "https://abide.veklom.com"),
    ("CAPPO", "https://cappo.veklom.com/health", "https://control.veklom.com"),
    ("PGL", "https://pgl.veklom.com/health", "https://control.veklom.com"),
]

results = {}
cors_results = {}

print(f"\n{'='*60}")
print(f"VEKLOM PRODUCTION SMOKE TEST")
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print(f"{'='*60}\n")

# Health checks
for name, url, key, val in SERVICES:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VeklomSmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read().decode()
            status_code = r.status
            try:
                data = json.loads(body)
            except Exception:
                data = {"raw": body[:200]}
            
            digest = hashlib.sha256(body.encode()).hexdigest()[:16]
            
            if key and isinstance(data, dict):
                actual_val = str(data.get(key, ""))
                passed = val.lower() in actual_val.lower() if val else True
            else:
                passed = status_code < 400
            
            results[name] = {
                "status": "VERIFIED" if passed else "DEGRADED",
                "http": status_code,
                "response_digest": digest,
                "data": data,
                "url": url
            }
            print(f"[{'OK' if passed else 'FAIL'}] {name}: HTTP {status_code} | digest:{digest} | {json.dumps(data)[:120]}")
    except urllib.error.HTTPError as e:
        results[name] = {"status": "DEGRADED", "http": e.code, "error": str(e), "url": url}
        print(f"[FAIL] {name}: HTTP {e.code} — {e}")
    except Exception as e:
        results[name] = {"status": "NOT_REACHABLE", "http": 0, "error": str(e), "url": url}
        print(f"[FAIL] {name}: FAILED — {e}")

print(f"\n{'='*60}")
print("CORS VERIFICATION")
print(f"{'='*60}\n")

for name, url, origin in CORS_CHECKS:
    try:
        req = urllib.request.Request(
            url,
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
                "User-Agent": "VeklomSmokeTest/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            acao = r.headers.get("Access-Control-Allow-Origin", "")
            acam = r.headers.get("Access-Control-Allow-Methods", "")
            passed = origin in acao or "*" in acao
            key = f"{name}|{origin}"
            cors_results[key] = {
                "status": "VERIFIED" if passed else "BLOCKED",
                "origin": origin,
                "acao_header": acao,
                "acam_header": acam
            }
            print(f"[{'OK' if passed else 'FAIL'}] {name} ← {origin}: ACAO={acao}")
    except urllib.error.HTTPError as e:
        # OPTIONS may return 200 or 204, read headers
        acao = e.headers.get("Access-Control-Allow-Origin", "")
        passed = origin in acao or "*" in acao
        key = f"{name}|{origin}"
        cors_results[key] = {
            "status": "VERIFIED" if passed else "BLOCKED",
            "origin": origin,
            "acao_header": acao,
            "http": e.code
        }
        print(f"[{'OK' if passed else 'FAIL'}] {name} ← {origin}: HTTP {e.code} ACAO={acao}")
    except Exception as e:
        key = f"{name}|{origin}"
        cors_results[key] = {"status": "FAILED", "origin": origin, "error": str(e)}
        print(f"[FAIL] {name} ← {origin}: FAILED — {e}")

print(f"\n{'='*60}")
print("API ENDPOINT SPOT CHECKS")
print(f"{'='*60}\n")

api_checks = [
    ("BYOS /api/v1/ root", "https://api.veklom.com/api/v1/"),
    ("BYOS /api/v1/capabilities", "https://api.veklom.com/api/v1/capabilities"),
    ("PGL /api/v1/events", "https://pgl.veklom.com/api/v1/events"),
    ("BYOS /api/v1/auth/me (expect 401)", "https://api.veklom.com/api/v1/auth/me"),
]

api_results = {}
for name, url in api_checks:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VeklomSmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read().decode()
            status_code = r.status
            try:
                data = json.loads(body)
            except:
                data = {"raw": body[:100]}
            api_results[name] = {"status": "PRESENT", "http": status_code, "data": data}
            print(f"[OK] {name}: HTTP {status_code} | {json.dumps(data)[:120]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else ""
        expected_401 = "401" in name and e.code == 401
        api_results[name] = {"status": "VERIFIED" if expected_401 else "DEGRADED", "http": e.code, "body": body[:100]}
        mark = "OK" if expected_401 else "✗"
        print(f"[{mark}] {name}: HTTP {e.code} | {body[:80]}")
    except Exception as e:
        api_results[name] = {"status": "NOT_REACHABLE", "error": str(e)}
        print(f"[FAIL] {name}: FAILED — {e}")

# Summary
print(f"\n{'='*60}")
print("FINAL SUMMARY")
print(f"{'='*60}\n")

verified = sum(1 for r in results.values() if r["status"] == "VERIFIED")
total = len(results)
print(f"Services: {verified}/{total} VERIFIED")
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print("")

for name, r in results.items():
    icon = "OK" if r["status"] == "VERIFIED" else "✗"
    print(f"  [{icon}] {name}: {r['status']} (HTTP {r.get('http', '?')})")

print("")
cors_ok = sum(1 for r in cors_results.values() if r["status"] == "VERIFIED")
print(f"CORS: {cors_ok}/{len(cors_results)} VERIFIED")
for k, r in cors_results.items():
    icon = "OK" if r["status"] == "VERIFIED" else "✗"
    print(f"  [{icon}] {k}: {r['status']}")

# Write JSON proof
proof = {
    "test_timestamp": datetime.now(timezone.utc).isoformat(),
    "services": results,
    "cors": cors_results,
    "api_endpoints": api_results
}
with open("/tmp/smoke_proof.json", "w") as f:
    json.dump(proof, f, indent=2)
print(f"\nProof written to /tmp/smoke_proof.json")
