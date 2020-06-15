from __future__ import print_function
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from datetime import date
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pytz

# notes are in OneNote - CS-Career - Interesting - 36Kr-Crawler-Calendar
# Current daily started running on 2020-06-14, which filled 2020-06-12

tag_start_with = "window.initialState="
calendar_id = '95nhljg3dp6ui5cojv2728n50o@group.calendar.google.com'
backfill_size = 800
backfill_timestamp = 1592097024336 # from this timestamp, day -20, return (backfill_size) passages. 
# 1592097024336 is Sunday, June 14, 2020 1:10:24.336 AM, and thus we get the lastest event is on April 14th, 2020.(done on that day)
# size = 20, is finished for 2020-03-18
# 氪星晚报 at most 793 条 
# size = 800, backfill done for 2017-10-27, and then google calendar returned error: googleapiclient.errors.HttpError: <HttpError 403 when requesting https://www.googleapis.com/calendar/v3/calendars/95nhljg3dp6ui5cojv2728n50o%40group.calendar.google.com/events?alt=json returned "Rate Limit Exceeded">
# [2017-10-27, 2020-04-14] is done

def calender_initiate():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)
    return service

# backfill
def backfill(url,service):
    payload = {"partner_id":"web","timestamp":1592097024336,"param":{"searchType":"article","searchWord":"氪星晚报","sort":"date","pageSize":backfill_size,"pageEvent":1,"pageCallback":"eyJmaXJzdElkIjo3MDg3ODM3ODMzNjkyMjIsImxhc3RJZCI6NjY3NjI0NjI3MDk5NjUwLCJmaXJzdENyZWF0ZVRpbWUiOjE1ODk1MzgwODQzNTMsImxhc3RDcmVhdGVUaW1lIjoxNTg3MTE5NTIyNjM2fQ","siteId":1,"platformId":2}}
    headers = {"content-type":'application/json','User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    r = requests.post(url,json = payload, headers = headers)

    # print (r.request.body)
    # print (r.request.headers)

    # print(r.json())

    result_list = r.json()['data']['itemList']
    event_days(result_list,service)


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

def verify_date(event_list, date_time,service):
    length_estimate = len(event_list) / 2 
    date = datetime.combine(date_time.date(), datetime.min.time())
    date_next = datetime.combine(date_time.date(), datetime.max.time())
    events_result = service.events().list(calendarId=calendar_id, 
                                        timeMin=date.isoformat() + 'Z', # 'Z' indicates UTC time,
                                        maxResults=length_estimate, singleEvents=True, timeMax = date_next.isoformat() + 'Z',
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    print('verify_date: ', date)
    if not events:
        # print('No upcoming events found.')
        print('should run script because no events are added')
        return True # No events added for that day. Should run the method to add.
    elif len(events) < length_estimate:
        print('should run script because less than estimate length events are added. Estimate length: ', length_estimate, 'actual length: ', len(events))
        return True
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])
    print(' should not run script because same amounts of events are added. Estimate length: ', length_estimate, 'actual length: ', len(events))
    return False

def add_event(event_list, date_time, service):
    # print(event_list)
    for i in range(0,len(event_list),2): 
    # use range seems brings many edge cases into bugs, it's better to have i be controlled by me, not by range()
    # filter the list first to avoid those edge cases.
        # print(event_list[i].a.string)
        # print(event_list[i+1].string)
        link_list = event_list[i].find_all('a')
        link_url = ''
        link_text = ''
        content = ''
        valid_event = False
        for link in link_list:
            if link.get('href'):
                link_url = link.get('href')
                link_text = link.string
                valid_event = True
        if i < len(event_list)-2: # acutally in filtering, we already ensure this is an even number list.
            content = event_list[i+1].text
        if not valid_event: 
            print ("not valid event, skip --> url: ", link_url, "title text: ", link_text, "content: ", content)
            continue
        event = {
          'summary': link_text,
          'description': content,
          'start': {
            'dateTime': date_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
          },
          'end': {
            'dateTime': date_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
          },
          'source': {
            'url': link_url
          } 
        }
        print(event)
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))


def add_to_calender(event_list, date_time, service):
    if verify_date(event_list, date_time, service):
        add_event(event_list, date_time, service)

def event_days(res_list,service):
    for res in res_list:
        event_day(res,service)

# See the edge cases below to know what this filter does
def filter_event_list(event_list):
    print('size before filtering: ',len(event_list))
    filtered_event_list = []
    for event in event_list:
        link_list = event.find_all('a')
        valid = False
        for link in link_list:
            if link.get('href') and link.string: # this is to avoid case #1
                valid = True
                break;
        if event.find('p', class_='img-desc') or event.find_all('img'): # to avoid case #2
            print('filtered img relevant: ', event.string)
            continue
        if valid or event.text:
           filtered_event_list.append(event)
        else :
            print('filtered no text relevant: ', event.string)
    print('size after filtering: ',len(filtered_event_list))
    current_len = len(filtered_event_list)
    if not current_len % 2 ==0: # even
        filtered_event_list.pop()
    return  filtered_event_list

# edge case #1: 
# <p><a href="https://36kr.com/newsflashes/665835410934530" target="_blank">Airbnb宣布获得10亿美元定期银团贷款</a></p> 
# <p><a href="http://v.t.sina.com.cn/share/share.php?appkey=595885820&amp;url=https://36kr.com/newsflashes/665835410934530&amp;title=Airbnb%E5%AE%A3%E5%B8%83%E8%8E%B7%E5%BE%9710%E4%BA%BF%E7%BE%8E%E5%85%83%E5%AE%9A%E6%9C%9F%E9%93%B6%E5%9B%A2%E8%B4%B7%E6%AC%BE"></a></p> 
# <p>36氪获悉，据Airbnb官方消息，Airbnb宣布从机构投资者获得10亿美元定期银团贷款。4月7日，Airbnb宣布，私募股权投资公司银湖和Sixth Street Partners将以债券加股权的形式对该公司投资10亿美元。<br></p> 

# We got the above part - 3 <p> as one calendar event, because the second <p><a> is not valid -- just a share url from the source
# should filter it out.

# edge case #2:
# <p><img src="https://img.36krcdn.com/20200415/v2_74730bfe814e4bbba464c30bc031f202_img_jpg" data-img-size-val="6281,4187"></p> 
# <p class="img-desc" label="图片描述" classname="img-desc">来源：pexels<br></p> 



def event_day(res_day, service):
    day_url = "https://36kr.com/p/" + str(res_day['itemId'])
    date_time = datetime.fromtimestamp(res_day['publishTime']/1000, pytz.timezone('Asia/Shanghai')) # from china timezone to UTC
    print('new_date: ', date_time)
    soup = soup_url(day_url)
    event_list = soup.find('div',class_='common-width content articleDetailContent kr-rich-text-wrapper').find_all('p', class_='') # all text i need is in this div
    filtered_list = filter_event_list(event_list)
    add_to_calender(filtered_list,date_time,service)
    # print(event_list)


def current(url,service):
    soup = soup_url(url)
    script_list = soup.find_all('script')
    result_tag = find_search_result(script_list)
    res_list = process_string(result_tag)
    event_day(res_list[0], service)



if __name__ == '__main__':
    crawler_url = 'https://36kr.com/search/articles/%E6%B0%AA%E6%98%9F%E6%99%9A%E6%8A%A5?sort=date'
    backfill_url = 'https://gateway.36kr.com/api/mis/nav/search/resultbytype'
    # run(url, end_id)
    # current(url, calender_initiate())
    backfill(backfill_url,calender_initiate())    
