import requests
from bs4 import BeautifulSoup
import json

tag_start_with = "window.initialState="

# backfill
def backfill():
	payload = {"partner_id":"web","timestamp":1592097024336,"param":{"searchType":"article","searchWord":"氪星晚报","sort":"date","pageSize":300,"pageEvent":1,"pageCallback":"eyJmaXJzdElkIjo3MDg3ODM3ODMzNjkyMjIsImxhc3RJZCI6NjY3NjI0NjI3MDk5NjUwLCJmaXJzdENyZWF0ZVRpbWUiOjE1ODk1MzgwODQzNTMsImxhc3RDcmVhdGVUaW1lIjoxNTg3MTE5NTIyNjM2fQ","siteId":1,"platformId":2}}
	headers = {"content-type":'application/json','User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
	r = requests.post('https://gateway.36kr.com/api/mis/nav/search/resultbytype',json = payload, headers = headers)

	# print (r.request.body)
	# print (r.request.headers)

	# print(r.json())

def soup_url(url):
	r = requests.get(url)
	# print (r.text)
	soup = BeautifulSoup(r.text, 'html.parser')
	# print(soup.title)
	# print(soup.find_all('script'))
	return soup

def find_search_result(list):
	for item in list:
		if item.string and item.string.startswith(tag_start_with):
			# print(item.string)
			return item.string

def process_string(string):
	json_string = string[len(tag_start_with):]
	# print(json_string)
	search_result = json.loads(json_string)
	res_list = search_result["searchResultData"]['data']['searchResult']['data']['itemList']
	# print(res_list)
	return res_list

def add_to_calender

def event_day(res_list):
	day = res_list[0]
	day_url = "https://36kr.com/p/" + str(day['itemId'])
	soup = soup_url(day_url)
	event_list = soup.find_all('p')
	print(event_list)




def current(url):
	soup = soup_url(url)
	script_list = soup.find_all('script')
	result_tag = find_search_result(script_list)
	res_list = process_string(result_tag)
	event_day(res_list)



if __name__ == '__main__':
	url = 'https://36kr.com/search/articles/%E6%B0%AA%E6%98%9F%E6%99%9A%E6%8A%A5?sort=date'
    # run(url, end_id)
	current(url)
