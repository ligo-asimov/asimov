"""
Review-related code.

Note
----
This code does not directly relate to the review of *asimov*
but rather to the review of events which it has been used to analyse.
"""

from datetime import datetime

STATES = {"REJECTED", "APPROVED", "PREFERRED", "DEPRECATED"}


class Review:
    """
    A class to record the review status of a given production.
    """
    def __init__(self):
        self.messages = []

    @classmethod
    def _from_dict(cls, message):
        """parse a dictionary into review"""
        messages = []
        for message in messages:
            self.messages.append(ReviewMessage.from_dict(message))
        review_ob = cls()
        review_ob.messages = messages
        return messages

class ReviewMessage:
    """
    A review message.
    """
    def __init__(self, message, production, state=None, timestamp=None):
        """
        Review messages are individual messages related to the review of a production.

        Parameters
        ----------
        message : str
           The review message. This can be free-form text.
        production : `Asimov.event.Production`
           The production which this message is attached to.
        state: str, {"REJECTED", "APPROVED", "PREFERRED", "DEPRECATED"}
           The review state. This is optional, and a message can
           be added without a review state. If a review state is added
           it will over-ride any previously added review messages.
        timestamp: str, optional
           The timestamp for the message, optional, should be
           formatted "%Y-%m-%d %H:%M:%S".
        """

        self.message = message

        if state.upper() in STATES:
            self.state = state.upper()
        else:
            raise ValueError(f"{state} is not a recognised review state.")

        if timestamp:
            self.timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = datetime.now()

    def to_dict(self):
        """
        Serialise this object as a dictionary
        """
        out = {}
        out['message'] = self.message
        out['timestamp'] = str(self.timestamp)
        out['state'] = self.state
        return out

    @classmethod
    def from_dict(cls, dictionary, production):
        """
        Create a review message from a dictionary.
        """
        default = {"state": None,
                   "message": None,
                   "timestamp": None}
        default = default.update(dictionary)
        message_ob = cls(message=default['message'],
                         production=production,
                         state=default['status'],
                         timestamp=default['timestamp'])
        return message_ob
