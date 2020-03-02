import requests
import json
from . import config

class Mattermost(object):

    def __init__(self, url=None):
        if not url:
            self.url = config.get("mattermost", "webhook_url")
        else:
            self.url = url

    def send_message(self, message, channel):
        self.submit_payload(message, channel)
            
    def submit_payload(self, message, channel=None):
        data = {"text": message}

        if channel:
            data['channel'] = channel
        
        response = requests.post(self.url, data=json.dumps(data),
                                 headers={"Content-Type": "application/json"})

        if response.status_code != 200:
            raise ValueError("Mattermost post failed")
