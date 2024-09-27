#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
redis_dump.py
'''
import json
import redis
from rejson import Client, Path

CACHE = []
cursor = 0
r = redis.StrictRedis(host='localhost', port=10001, db=0, password="shorturl")
while True:
    cursor, keys = r.scan(cursor=cursor)
    for key in keys:
        key = key.decode('utf-8')
        if key.startswith(":src.schema.Url:") and key != ":src.schema.Url:index:hash":
            CACHE.append(key)
    if cursor == 0:
        break
print('Total key number: ', len(CACHE))

JsonData = []
rj = Client(host='localhost', port=10001, decode_responses=True)
for key in CACHE:
    value = rj.jsonget(key, Path.rootPath())
    JsonData.append(value)

with open('dump_links.json', 'w') as f:
    json.dump(JsonData, f)