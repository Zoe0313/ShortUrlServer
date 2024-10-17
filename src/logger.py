#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
logger.py
'''

import logging
import logging.handlers
import os

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s"

def createMailHandler():
   mail_handler = logging.handlers.SMTPHandler(
       mailhost=('smtp.gmail.com', 587),
       fromaddr='xiaoxia.liu@broadcom.com',
       toaddrs=['xiaoxia.liu@broadcom.com', 'essen.yu@broadcom.com'],
       subject='Application Error',
       credentials=("xiaoxia.liu@broadcom.com", "wakk txlp quul jtmk")
   )
   mail_handler.setLevel(logging.ERROR)
   mail_handler.setFormatter(logging.Formatter(LOG_FORMAT))
   return mail_handler

def initLogger():
    if os.environ.get('STAGE') == 'product':
        logFile = 'shorturl-service-prd.log'
    else:
        logFile = 'shorturl-service-stg.log'
    dirPath = os.path.join(os.path.abspath(__file__).split("/src")[0], 'persist')
    os.makedirs(dirPath, exist_ok=True)
    logFile = os.path.join(dirPath, logFile)
    
    logger = logging.getLogger('mylogger')
    logger.setLevel(logging.INFO)
    handler = logging.handlers.TimedRotatingFileHandler(logFile, when='midnight', interval=1, backupCount=7)
    formatter = logging.Formatter(fmt=LOG_FORMAT)
    formatter.default_time_format = '%Y-%m-%dT%H:%M:%S'
    formatter.default_msec_format = '%s.%03d'
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
