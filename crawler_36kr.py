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

tag_start_with = "window.initialState="
calendar_id = '95nhljg3dp6ui5cojv2728n50o@group.calendar.google.com'

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
    payload = {"partner_id":"web","timestamp":1592097024336,"param":{"searchType":"article","searchWord":"氪星晚报","sort":"date","pageSize":2,"pageEvent":1,"pageCallback":"eyJmaXJzdElkIjo3MDg3ODM3ODMzNjkyMjIsImxhc3RJZCI6NjY3NjI0NjI3MDk5NjUwLCJmaXJzdENyZWF0ZVRpbWUiOjE1ODk1MzgwODQzNTMsImxhc3RDcmVhdGVUaW1lIjoxNTg3MTE5NTIyNjM2fQ","siteId":1,"platformId":2}}
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
    date = datetime.combine(date_time.date(), datetime.min.time())
    date_next = datetime.combine(date_time.date(), datetime.max.time())
    events_result = service.events().list(calendarId=calendar_id, 
                                        timeMin=date.isoformat() + 'Z', # 'Z' indicates UTC time,
                                        maxResults=1, singleEvents=True, timeMax = date_next.isoformat() + 'Z',
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        # print('No upcoming events found.')
        print('verify_date: ', date, ' should run script')
        return True # No events added for that day. Should run the method to add.
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])
    print('verify_date: ', date, ' should not run script')
    return False

# for backfill, if on that day, >= 10 events are returned, then we will skip that day.
def backfill_verify_date(date_time,service):
    date = datetime.combine(date_time.date(), datetime.min.time())
    date_next = datetime.combine(date_time.date(), datetime.max.time())
    events_result = service.events().list(calendarId=calendar_id, 
                                        timeMin=date.isoformat() + 'Z', # 'Z' indicates UTC time,
                                        maxResults=10, singleEvents=True, timeMax = date_next.isoformat() + 'Z',
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events or len(events) < 10:
        # print('No upcoming events found.')
        print('verify_date: ', date, ' should run script')
        return True # No events added for that day. Should run the method to add.
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])
    print('verify_date: ', date, ' should not run script')
    return False

def add_event(event_list, date_time, service):
    # print(event_list)
    for i in range(0,len(event_list),2):
        # print(event_list[i].a.string)
        # print(event_list[i+1].string)
        link_list = event_list[i].find_all('a')
        link_url = ''
        link_text = ''
        for link in link_list:
            if link.get('href'):
                link_url = link.get('href')
                link_text = link.string
        event = {
          'summary': link_text,
          'description': event_list[i+1].text,
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
        # print(event)
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))


def add_to_calender(event_list, date_time, service):
    if verify_date(event_list, date_time, service):
        add_event(event_list, date_time, service)

def event_days(res_list,service):
    for res in res_list:
        event_day(res,service)

def event_day(res_day, service):
    day_url = "https://36kr.com/p/" + str(res_day['itemId'])
    date_time = datetime.fromtimestamp(res_day['publishTime']/1000, pytz.timezone('Asia/Shanghai')) # from china timezone to UTC
    print('new_date: ', date_time)
    soup = soup_url(day_url)
    event_list = soup.find('div',class_='common-width content articleDetailContent kr-rich-text-wrapper').find_all('p') # all text i need is in this div
    add_to_calender(event_list,date_time,service)
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
