import urllib.request, json
urllib.request.getproxies = lambda: {}
req = urllib.request.Request(
    'http://127.0.0.1:8020/',
    data=json.dumps({
        'action': 'validate_consequence',
        'consequence_request': {
            'execution_id': 'VFRAC_SUBSTRATE_HEALING',
            'epoch': 1,
            'holder_id': 'MARS_PRIMARY_WORKER',
            'operation_id': 'OP_PRIMARY_001',
            'signing_key_public': 'pub',
            'state_root': 'root',
            'evidence_head': 'head',
            'payload_digest': 'dig',
            'signature': 'sig'
        }
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print(r.read())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read())
except Exception as e:
    print('Exception:', e)
