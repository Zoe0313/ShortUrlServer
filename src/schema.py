#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.
schema.py
'''

import datetime
from redis_om import (EmbeddedJsonModel, Field, JsonModel, HashModel)
from pydantic import PositiveInt, EmailStr
from typing import Optional, List
from enum import Enum

NumOfDaysDeterminedAsDeactivated = 90

class STATUS(Enum):
   CREATED = 0
   USED = 1
   DEACTIVATED = 2
   DELETED = 3

class Url(JsonModel):
    original_url: str
    hash_original: str = Field(index=True)
    short_key: str = Field(index=True)
    create_at: datetime.date = Field(index=True)
    status: Optional[int] = Field(index=True)
    expire_time: Optional[datetime.date] = None
    user_id: Optional[str] = Field(index=True)
    customize: Optional[bool] = Field(index=True)
    utilization: Optional[int] = 0
    lastRedirectTime: Optional[datetime.datetime] = None
    # email: EmailStr
