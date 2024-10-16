#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
utils.py
'''

import datetime
from dateutil import relativedelta
import hashlib
import re
from urllib.parse import urlparse

def type2date(expireType):
    date = None
    today = datetime.datetime.utcnow().date()
    if expireType == '1month':
        date = today + relativedelta.relativedelta(months=1)
    elif expireType == '3month':
        date = today + relativedelta.relativedelta(months=3)
    elif expireType == '6month':
        date = today + relativedelta.relativedelta(months=6)
    elif expireType == '1year':
        date = today + relativedelta.relativedelta(years=1)
    elif expireType == 'indefinitely':
        date = None
    return date

def validateCharacters(shortKey):
    finds = re.findall(r'[^a-zA-Z0-9\-\_]', shortKey)
    if len(finds) > 0:
        raise Exception('The characters in short ID should be picked from [A-Za-z0-9_-].')

def validateUrl(url):
    result = urlparse(url)
    if len(result.scheme) == 0 or len(result.netloc) == 0:
        raise Exception("Please follow the syntax specifications in RFC 1808 to input url")

def url2hash(url: str) -> str:
    hash_object = hashlib.sha256(url.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex

