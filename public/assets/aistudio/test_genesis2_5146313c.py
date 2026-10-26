import urllib.request, json
urllib.request.getproxies = lambda: {}
req = urllib.request.Request(
    'http://192.168.2.28:8020/',
    data=json.dumps({'action': 'register_genesis', 'execution_id': 'TEST_GEN', 'epoch': 1, 'holder': 'HOLDER', 'pub_key': 'pub'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print(r.status, r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode('utf-8'))
except Exception as e:
    print('Exception:', e)
