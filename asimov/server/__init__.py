"""
The asimov server
-----------------
This feature allows asimov to monitor and interact with ongoing
analyses without the need for an ongoing cronjob.
"""
from flask import Flask

from flask.json import JSONEncoder
from datetime import date

from . import logging
from . import basic

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
    
    app.json_encoder = CustomJSONEncoder

    app.register_blueprint(logging.bp)
    app.register_blueprint(basic.bp)
    
    return app


def bootstrap():
    app = create_app()
    app.run(debug=False)


if __name__ == '__main__':
    bootstrap()
