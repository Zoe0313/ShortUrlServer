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
    logger = logging.getLogger('mylogger')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(fmt=LOG_FORMAT)
        formatter.default_time_format = '%Y-%m-%dT%H:%M:%S'
        formatter.default_msec_format = '%s.%03d'
        # StreamHandler: Logs to stdout (console)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # FileHandler: Logs to a file
        stage = 'prd' if os.environ.get('STAGE') == 'product' else 'stg'
        log_file = f'shorturl-service-{stage}.log'
        dir_path = os.path.join(os.path.abspath(__file__).split("/src")[0], 'persist')
        os.makedirs(dir_path, exist_ok=True)
        log_file = os.path.join(dir_path, log_file)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
