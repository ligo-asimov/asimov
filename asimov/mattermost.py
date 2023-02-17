import json

import requests

from . import config


class Mattermost(object):
    def __init__(self, url=None):
        if not url:
            self.url = config.get("mattermost", "webhook_url")
        else:
            self.url = url

    def send_message(self, message, channel=None):
        """
        Send a message to a chat channel.

        Parameters
        ----------
        message : str
           The text of the message.
        channel : str, optional
           The name of the channel.
           To send a direct message to a person prefix their username with
           an @ sign. Defaults to the default channel set in mattermost
           for the webhook.
        """
        self.submit_payload(message, channel)

    def submit_payload(self, message, attachments=None, props=None, channel=None):
        """
        Send a payload (normally a message) to a chat channel.

        Parameters
        ----------
        message : str
           The text of the message.
        channel : str, optional
           The name of the channel.
           To send a direct message to a person prefix their username with
           an @ sign. Defaults to the default channel set in mattermost
           for the webhook.
        """
        data = {"text": message, "attachments": [attachments], "props": props}

        if channel:
            data["channel"] = channel

        response = requests.post(
            self.url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            raise ValueError("Mattermost post failed")
