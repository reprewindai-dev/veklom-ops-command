import urllib.request, json
urllib.request.getproxies = lambda: {}
body = json.dumps({"action": "register", "execution_id": "TEST2", "epoch": 1, "pub_key": "pub"}).encode()
req = urllib.request.Request("http://192.168.2.28:8020", data=body, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
