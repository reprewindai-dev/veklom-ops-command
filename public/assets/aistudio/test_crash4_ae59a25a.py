import urllib.request, json
urllib.request.getproxies = lambda: {}
req = urllib.request.Request(
    'http://192.168.2.28:8020/',
    data=json.dumps({'action': 'validate_recursive_consequence'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print(r.read())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
except Exception as e:
    print('Exception:', e)
