import requests

# backfill
payload = {"partner_id":"web","timestamp":1592097024336,"param":{"searchType":"article","searchWord":"氪星晚报","sort":"date","pageSize":300,"pageEvent":1,"pageCallback":"eyJmaXJzdElkIjo3MDg3ODM3ODMzNjkyMjIsImxhc3RJZCI6NjY3NjI0NjI3MDk5NjUwLCJmaXJzdENyZWF0ZVRpbWUiOjE1ODk1MzgwODQzNTMsImxhc3RDcmVhdGVUaW1lIjoxNTg3MTE5NTIyNjM2fQ","siteId":1,"platformId":2}}
headers = {"content-type":'application/json','User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
r = requests.post('https://gateway.36kr.com/api/mis/nav/search/resultbytype',json = payload, headers = headers)

# print (r.request.body)
# print (r.request.headers)

print (r.json())

