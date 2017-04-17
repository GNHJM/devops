#!/usr/bin/env python
#-*-encoding:utf-8-*-
"""
DESCRIPTION : THIS PROGRAM WILL GET ALL PYTHON AWESOME PROJECT'S INFOMETHON, YOU CAN SAVE IT AS YOU WISH.
AUTHOR      : MIKE
DATE        : 2017/04/15
"""

from time import gmtime,strftime
from bs4 import BeautifulSoup
from Queue import Queue
from threading import Thread
import requests

github_queue = Queue()
result_queue = Queue()
AWESOME_PROJECT_ROOTURL='https://github.com/vinta/awesome-python'
NUM_THREADS = 20

def log(message,err=False,detail=''):
    current = strftime("%Y-%m-%d %H:%M:%S",gmtime())
    if err is True:
        print '[x]{} {} {}'.format(current,message,detail)
    else:
        print '[*]{} {}'.format(current,message)

def parser_projects(projects,category,description=''):
    for p in projects.find_all('li'):
        url = p.find('a').get('href')
        info = p.get_text().split('-')
        detail = ''
        if len(info) == 2:
            detail = info[1]
        title = info[0]

        github_queue.put({
            "category":category,
            "github":True if url.startswith('https://github.com') else False,
            "description":description,
            "title":title,
            "detail":detail,
            "url":url
            })

def awesome_projects_parser(htmlContent):
    soup = BeautifulSoup(htmlContent,'html.parser')
    for h2 in soup.find('article').find_all('h2'):
       category = h2.get_text()
       projects = h2.find_next('ul')
       description = h2.find_next('p')
       if description.find_next('ul') == h2.find_next('ul'):
           parser_projects(projects,category,description.string)
       else:
           parser_projects(projects,category,'')
def get_github_star(item):
    try:
        r = requests.get(item['url'])
        if r.status_code == 200 and r.content is not None:
            soup = BeautifulSoup(requests.get(item['url']).content,"html5lib")
            info_bar = soup.find('ul',{'class':'pagehead-actions'})
            item["star"] = int(filter(str.isdigit,str(info_bar.find_all('li')[1].get_text())))
            item["fork"] = int(filter(str.isdigit,str(info_bar.find_all('li')[2].get_text())))
        else:
            log('Query Error',True,r.status_code)
    except:
        item["error"]='QueryException'
    finally:
        return item

def print_result():
    while True:
        item=result_queue.get()
        print item
        result_queue.task_done()
        
def fetch_thread(index):
    while True:
        item = github_queue.get()
        if item.has_key('github') and item['github'] is True and item.has_key('url') and item['url'] is not None:
            item=get_github_star(item)
        result_queue.put(item)
        github_queue.task_done()
def main():
    r = requests.get(AWESOME_PROJECT_ROOTURL)
    if r.status_code == 200 and r.content is not None:
        awesome_projects_parser(r.content)
    else:
        log('Exit',True,r.status_code)
    
    # create some threads to query information
    for i in range(NUM_THREADS):
        t = Thread(target=fetch_thread,args=(i,))
        t.daemon=True
        t.start()
    # Create print thread for show the result in console or pipe to file
    print_result_thread = Thread(target=print_result)
    print_result_thread.daemon=True
    print_result_thread.start()

    github_queue.join()
    result_queue.join()

if __name__ == '__main__':
    main()

        