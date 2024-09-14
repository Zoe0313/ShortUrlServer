#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
utils.py
'''

import datetime
from dateutil import relativedelta
import hashlib
import base64
import re
from urllib.parse import urlparse
import functools
import time

def type2date(expireType):
    date = None
    if expireType == '1month':
        date = datetime.date.today() + relativedelta.relativedelta(months=1)
    elif expireType == '3month':
        date = datetime.date.today() + relativedelta.relativedelta(months=3)
    elif expireType == '6month':
        date = datetime.date.today() + relativedelta.relativedelta(months=6)
    elif expireType == '1year':
        date = datetime.date.today() + relativedelta.relativedelta(years=1)
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

def checkBroadcomUrlAccess(url):
    result = urlparse(url)
    if 'broadcom' in result.netloc:
        try:
            requests.get(url, timeout=5)
        except:
            return "Maybe the short url couldn't redirect to the BC url currently."
    return ""

def url2hash(url: str) -> str:
    hash_object = hashlib.sha256(url.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex

def logExecutionTime(func):
   @functools.wraps(func)
   def wrapper(*args, **kwargs):
      startTime = time.perf_counter()
      res = func(*args, **kwargs)
      endTime = time.perf_counter()
      output = '[{}] took {:.3f}s'.format(func.__name__, endTime - startTime)
      print(output)
      return res
   return wrapper
