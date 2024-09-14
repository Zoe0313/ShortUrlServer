#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
constant.py
'''

import os
import json
from dotenv import load_dotenv
load_dotenv()

SHORT_KEY_GENERATION_RETRIES_COUNT = int(os.getenv('SHORT_KEY_GENERATION_RETRIES_COUNT'))
SHORT_URL_LENGTH = int(os.getenv('SHORT_URL_LENGTH'))
ALIAS_URL_MIN_LENGTH = int(os.getenv('ALIAS_URL_MIN_LENGTH'))
ALIAS_URL_MAX_LENGTH = int(os.getenv('ALIAS_URL_MAX_LENGTH'))
SHORT_KEY_PREFIX = os.getenv('SHORT_KEY_PREFIX')
REDIS_OM_URL = os.getenv('REDIS_OM_URL')
ADMIN_USER_ID = json.loads(os.getenv('ADMIN_USER_ID'))
