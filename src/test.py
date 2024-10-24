#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
test.py
'''

import requests
import json
import os
from constant import SHORT_KEY_PREFIX

API = 'https://vsanvia.broadcom.net/api/'
print(API)

def get_short_url(long_url, short_key, expire_type, user_id):
    payload = {'original_url': long_url,
               'short_key': short_key,
               'expire_type': expire_type,
               'user_id': user_id}
    response = requests.post(url=API + 'shorten',
                             data=json.dumps(payload),
                             verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f"== Create a short url: {data['short_url']} ==")
        return data
    raise Exception(f'fail to get short url [{response.status_code}] {response.json()}')

def redirect_by_short_url(short_url):
    response = requests.get(short_url, allow_redirects=False, verify=False)
    if response.status_code == 302:
        long_url = response.headers.get('location')
        print('-> redirect to:', long_url)
        return long_url
    raise Exception(f'fail to get long url [{response.status_code}] {response.json()}')

def query_url_details_by_id(url_id):
    response = requests.get(url=API + 'url/' + url_id, verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f'== Query url detail by id {url_id} ==')
        for key, value in data.items():
            print(key + ': ' + str(value))
        return data
    raise Exception(f'fail to get url details [{response.status_code}]')

def delete_url_by_id(url_id):
    response = requests.delete(url=API + 'url/' + url_id, verify=False)
    if response.status_code == 200:
        return
    raise Exception(f'fail to delete url [{response.status_code}]')

def get_urls_by_user(user_id):
    response = requests.get(url=API + f'urls?user={user_id}', verify=False)
    if response.status_code == 200:
        results = response.json()
        urls = results['results']
        print(f"== The number of {user_id}'s urls is {len(urls)} ==")
        for url in urls:
            print(url['pk'], url['short_url'], url['expire_time'])
        return urls
    raise Exception(f"fail to query {user_id}'s urls [{response.status_code}]")

def get_urls_by_longurl(longUrl):
    payload = {'original_url': longUrl}
    response = requests.get(url=API + 'longurl', data=json.dumps(payload), verify=False)
    if response.status_code == 200:
        results = response.json()
        urls = results['results']
        print(f"== The number of urls found by long url is {len(urls)} ==")
        for url in urls:
            print(url['pk'], url['short_url'], url['expire_time'])
        return urls
    raise Exception(f"fail to query urls [{response.status_code}]")

def update_longurl_by_id(url_id, long_url):
    payload = {'original_url': long_url}
    response = requests.post(url=API + 'url/' + url_id,
                             data=json.dumps(payload),
                             verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f'== Update long url by id {url_id} ==')
        return data
    raise Exception(f'fail to update the long url by id [{response.status_code}] {response.json()}')

def update_longurl_by_shortkey(short_key, long_url):
    payload = {'short_key': short_key,
               'original_url': long_url}
    response = requests.post(url=API + 'longurl',
                             data=json.dumps(payload),
                             verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f"== Update long url by short key [{short_key}] ==")
        return data
    raise Exception(f'fail to update the long url by short key [{response.status_code}] {response.json()}')

def get_urls_by_shortkey(short_key):
    response = requests.get(url=API + f'shortkey/{short_key}', verify=False)
    if response.status_code == 200:
        results = response.json()
        urls = results['results']
        print(f"== The number of urls found by short key is {len(urls)} ==")
        for url in urls:
            print(url['pk'], url['short_url'], url['expire_time'])
        return urls
    raise Exception(f"fail to query urls by short key [{response.status_code}]")

def update_shortkey_by_id(url_id, short_key):
    response = requests.post(url=API + f'shortkey/{url_id}/{short_key}', verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f'== Update short key [{short_key}] by id {url_id} ==')
        return data
    raise Exception(f'fail to update the short key by id [{response.status_code}] {response.json()}')

def clearAll(testUser):
    print(f"== Clear all urls of user {testUser} ==")
    urls = get_urls_by_user(testUser)
    for url in urls:
        delete_url_by_id(url['pk'])

if __name__ == "__main__":
    testUser = 'lzoe'
    clearAll(testUser)
    # create a short url by customized short key
    testUrl = 'https://vmw-confluence.broadcom.net/display/vSANSHQE/Telemetry+Test+for+Global+Dedup'
    testShortkey = 'globaldedup'
    testExp = '1month'
    result = get_short_url(testUrl, testShortkey, testExp, testUser)
    shortUrl = result['short_url']
    urlId = result['url_id']
    print(urlId)
    redirect_by_short_url(shortUrl)
    # update the long url by short key
    testAnotherUrl = 'https://vmw-confluence.broadcom.net/display/SABU/vSAN+Short+URL+Service'
    update_longurl_by_shortkey(testShortkey, testAnotherUrl)
    redirect_by_short_url(shortUrl)
    # update the long url by url id
    testAnotherUrl = 'https://lvn-dbc2443.lvn.broadcom.net/js032470/public_html/'
    update_longurl_by_id(urlId, testAnotherUrl)
    redirect_by_short_url(shortUrl)
    # update short key by url id
    testAnotherShortkey = 'lvn-dbc-js'
    result = update_shortkey_by_id(urlId, testAnotherShortkey)
    shortUrl = result['short_url']
    redirect_by_short_url(shortUrl)
    # query the url detail
    query_url_details_by_id(urlId)
    # query url list by user
    get_urls_by_user(testUser)
    # query url list by long url
    get_urls_by_longurl(testAnotherUrl)
    # query url list by short key
    get_urls_by_shortkey(testAnotherShortkey)
    # test the utilization of redirect this short url
    # for _ in range(10):
    #     redirect_by_short_url('http://127.0.0.1:5000/HELLO-url')
    # query_url_details_by_id('01J5Z5Y1T5G5BVXCJ5XT8SGPTA')
    # # generate short url by broadcom url. check the response data contain warning message.
    # broadcomUrl = 'https://jenkins-vcf-vsan-shanghai-cycle.devops.broadcom.net/'
    # testShortkey = 'test-bc-url'
    # testExp = '1month'
    # result = get_short_url(broadcomUrl, testShortkey, testExp, testUser)
    # print(result)
