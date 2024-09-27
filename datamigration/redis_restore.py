#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
redis_restore.py
'''
import json
import requests

with open('dump_links.json', 'r') as f:
    JsonData = json.load(f)

def get_short_url(long_url, short_key, expire_type, user_id):
    payload = {'original_url': long_url,
               'short_key': short_key,
               'expire_type': expire_type,
               'user_id': user_id}
    response = requests.post(url='https://vsanvia.broadcom.net/api/shorten',
                             data=json.dumps(payload), verify=False)
    if response.status_code == 200:
        print(response.json())
        return
    raise Exception(f'fail to get short url [{response.status_code}] {response.json()}')


print(len(JsonData))
for data in JsonData:
    original_url = data["original_url"]
    short_key = data["short_key"]
    expire_time = data["expire_time"]
    user = data["user_id"]
    original_url = original_url.replace("confluence.eng.vmware.com", "vmw-confluence.broadcom.com")
    original_url = original_url.replace("bugzilla.eng.vmware.com", "bugzilla-vcf.lvn.broadcom.net")
    original_url = original_url.replace("jira.eng.vmware.com", "vmw-jira.broadcom.com")
    print(original_url, short_key, user)
    get_short_url(original_url, short_key, 'indefinitely', user)
