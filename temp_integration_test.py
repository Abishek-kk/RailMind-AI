import os
import time
import json
import requests
import cv2
import numpy as np

path = 'backend/data/mock_feeds/integration_test.mp4'
os.makedirs(os.path.dirname(path), exist_ok=True)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(path, fourcc, 5.0, (320, 240))
for i in range(10):
    frame = np.full((240, 320, 3), 255 if i % 2 == 0 else 0, np.uint8)
    out.write(frame)
out.release()

feed_id = f'integration_{int(time.time())}'
url = 'http://127.0.0.1:8000/api/feeds/upload'
with open(path, 'rb') as f:
    resp = requests.post(url, files={'file': ('integration_test.mp4', f, 'video/mp4')}, params={'feed_id': feed_id, 'name': 'Integration Test Feed'})
print('upload status', resp.status_code)
print(resp.text)
data = resp.json()
print('feed_id', data.get('feed_id'))
print('feeds status', requests.get('http://127.0.0.1:8000/api/feeds').status_code)
print('feeds', requests.get('http://127.0.0.1:8000/api/feeds').json())
print('stream status', requests.get(f'http://127.0.0.1:8000/api/feeds/{feed_id}/stream').status_code)
print('stream', requests.get(f'http://127.0.0.1:8000/api/feeds/{feed_id}/stream').json())
print('dashboard status', requests.get('http://127.0.0.1:8000/api/dashboard/cctv-summary').status_code)
del_resp = requests.delete(f'http://127.0.0.1:8000/api/feeds/{feed_id}')
print('delete', del_resp.status_code)
print('feeds-after', requests.get('http://127.0.0.1:8000/api/feeds').json())
