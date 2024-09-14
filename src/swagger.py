#!/usr/bin/env python

# Copyright 2023 VMware, Inc.  All rights reserved. -- VMware Confidential

'''
Module docstring.  
swagger.py
'''

import yaml
import json
from flask_swagger_ui import get_swaggerui_blueprint
import os

def initSwaggerUI(app):
    projectDir = os.path.abspath(__file__).split("/src")[0]
    swagger_yaml_path = os.path.join(projectDir, 'doc/swagger.yml')
    with open(swagger_yaml_path, 'r') as file:
        swagger_documentation = yaml.safe_load(file)
    # convert YAML to JSON and save it to a file
    swagger_json_path = os.path.join(projectDir, 'static/swagger.json')
    with open(swagger_json_path, 'w') as file:
        json.dump(swagger_documentation, file)

    swagger_ui_blueprint = get_swaggerui_blueprint(
        base_url="/swagger",
        api_url="/static/swagger.json",
        config={'app_name': 'URL Shortener API'}
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix='/swagger')
