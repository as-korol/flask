import requests
import os
import base64

for path in ['/', '/data_to', '/net', '/apixml']:
    r = requests.get(f'http://localhost:5000{path}')
    print(path, r.status_code)

with open(os.path.join('static', 'image0008.png'), 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')
res = requests.post('http://localhost:5000/apinet', json={'imagebin': b64})
print('/apinet', res.status_code, res.json())