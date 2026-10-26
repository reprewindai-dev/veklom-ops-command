import time
import json
import urllib.request
import datetime
import sys

def fetch_status(port):
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:{port}/status', timeout=2)
        return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("==================================================")
print(" EARTH POLAR TELEMETRY POLLER (60-SECOND INTERVAL)")
print("==================================================")
sys.stdout.flush()

while True:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sink = fetch_status(8040)
    cappo = fetch_status(8050)
    cont = fetch_status(8060)
    
    # Try getting the counters directly if available
    sink_count = sink.get("counter", len(sink.get("applied_operations", []))) if "error" not in sink else "ERR"
    
    out = f"[{ts}] SINK_OPS: {sink_count} | CAPPO: {'ALIVE' if 'error' not in cappo else 'ERR'} | CONTINUUM: {'ALIVE' if 'error' not in cont else 'ERR'}"
    print(out)
    sys.stdout.flush()
    time.sleep(60)
