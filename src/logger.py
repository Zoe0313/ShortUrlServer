#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
logger.py
'''

import datetime
import logging
import logging.handlers
import os
from flask.logging import default_handler

def createMailHandler():
   mail_handler = logging.handlers.SMTPHandler(
       mailhost=('smtp.gmail.com', 587),
       fromaddr='xiaoxia.liu@broadcom.com',
       toaddrs=['xiaoxia.liu@broadcom.com', 'essen.yu@broadcom.com'],
       subject='Application Error',
       credentials=("xiaoxia.liu@broadcom.com", "wakk txlp quul jtmk")
   )
   mail_handler.setLevel(logging.ERROR)
   mail_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
   return mail_handler

def initLogger():
    logger = logging.getLogger('myLogger')  # my logger
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        file_handler = logging.FileHandler('url-shortener.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
