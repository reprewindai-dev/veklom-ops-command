import time
import json
import urllib.request
import datetime
import sys

def fetch_status(port, path='/status'):
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=2)
        return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("==================================================")
print(" EARTH 30-SECOND RAW STRESS TELEMETRY POLLER")
print("==================================================")
sys.stdout.flush()

while True:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sink = fetch_status(8040)
    
    # Try getting the counters
    sink_count = sink.get("counter", len(sink.get("applied_operations", []))) if "error" not in sink else "ERR"
    
    out = f"[{ts}] SINK_OPS: {sink_count}"
    print(out)
    sys.stdout.flush()
    time.sleep(30)
