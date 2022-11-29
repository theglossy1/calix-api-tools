"""
Simple script to see how each ONT is attached to its OLT (serial-number or reg-id)

Written by Matt Glosson on 11/28/2022 and tested on Python 3.10.7 for Windows
"""

import json
import logging
import re

try:
    import requests
except ModuleNotFoundError as e:
    print(f'Failed: {e}. Please install required modules by running:\n\tpython -m pip install -r requirements.txt')
    quit(1)

from requests.auth import HTTPBasicAuth

smx_server = '192.0.2.52'     # IP address or hostname
smx_username = 'admin'
smx_password = 'test123'
device_name = 'Antwerp_E7_02' # OLT name

CMD = "show ont linkage"      # This is obviously critical to the way the program works

def parse_ont_linkages(result: str) -> dict:
    """
    Reads in a string and returns a list:
        {
          <name>: {
            status: <Confirmed|Not-Linked>,
            linked-by: <Serial-Number|Reg-ID>
          }
        }
    """
    # The below monstrosity splits all ONTs out and removes any empty items
    ont_list = re.split(r'^(?=ont [\S]+)', result, re.M)[1:]

    ont_dict = {}
    ont_name = ''
    ont_status = ''

    for ont_item in ont_list:
        ont_linkage = ont_item.split('\n')
        for ont_attrib in ont_linkage:
            if ont_attrib.startswith('ont '):
                ont_name = ont_attrib[4:]
                ont_dict[ont_name] = {}
            elif ont_attrib.startswith('  status'):
                ont_status = ont_attrib[8:]
                ont_dict[ont_name]['status'] = ont_status.strip()
            elif ont_attrib.startswith('  linked-by'):
                ont_linked_by = ont_attrib[11:]
                ont_dict[ont_name]['linked-by'] = ont_linked_by.strip()

    return ont_dict


request_body_dict = {
    "deviceName": device_name,
    "operator": "READ",
    "cmd": CMD
}

url = f'https://{smx_server}:18443/rest/v1/config/device/{device_name}/cli'
headers = { "content-type": "application/json" }
creds = HTTPBasicAuth(smx_username, smx_password)
json_body = json.dumps(request_body_dict)

# Don't disable warnings, but capture them to whatever logging you might want to add
# This is usually necessary because very few SMx installations have a valid certificate
logging.captureWarnings(True)

# Execute the actual API call. As above, because SMx likely doesn't have a valid certificate, 'verify' is set to False
try:
    r = requests.post(url, headers=headers, auth=creds, data=json_body, verify=False)
except requests.exceptions.ConnectionError:
    print(f'Fatal error: Could not connect to {url}')
    quit(2)
except Exception as e:
    print(f'Fatal error: {e}')
    quit(2)

if r.status_code == 200:
    payload = json.loads(r.text)
    linkages = parse_ont_linkages(payload['result'])
    print(json.dumps(linkages, indent=2))
else:
    print(f'Error: Received status code of {r.status_code} ({r.text}) from SMx. Status code of 200 is required.')
