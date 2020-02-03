import requests
import json
from . import config

class Mattermost(object):

    def __init__(self, url=None):
        if not url:
            self.url = config.get("mattermost", "webhook_url")
        else:
            self.url = url

    def submit_payload(self, message):
        data = {"text": message}
    
        response = requests.post(self.url, data=json.dumps(data),
                                 headers={"Content-Type": "application/json"})

        if response.status_code != 200:
            raise ValueError("Mattermost post failed")
