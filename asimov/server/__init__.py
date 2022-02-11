"""
The asimov server
-----------------
This feature allows asimov to monitor and interact with ongoing
analyses without the need for an ongoing cronjob.
"""
from flask import Flask

import asimov.server.ledger
import asimov.server.productions


from flask.json import JSONEncoder
from datetime import date


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def create_app():
    """
    Create the web app for asimov
    """
    app = Flask("asimov")
    app.register_blueprint(asimov.server.ledger.events_bp)
    app.register_blueprint(asimov.server.productions.prods_bp)

    app.json_encoder = CustomJSONEncoder
    return app
