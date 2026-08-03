import requests
url = 'http://localhost:8000/uploads/AdobeStock_206827806_Video_HD_Preview_AdobeStock_206827806_Video_HD_Preview.mov'
r = requests.get(url, timeout=10)
print('status', r.status_code)
print('headers', dict(r.headers))
print('text', r.text[:200])
