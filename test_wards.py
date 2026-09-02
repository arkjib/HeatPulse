import urllib.request, json
req = urllib.request.urlopen('http://localhost:8000/api/v1/wards/weather')
d = json.loads(req.read())
print('Wards count:', d['ward_count'])
print('Successful:', d['successful_wards'])
print('Failed:', d['failed_wards'])
if d['successful_wards'] > 0: print(d['wards'][0])
