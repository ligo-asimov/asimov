"""
Basic endpoints for asimov
==========================

This module implements endpoints which don't handle data, but instead provide things like returning the current version data for things like asimov and the various pipelines.

"""

from flask import Blueprint, request, jsonify, make_response

import asimov

bp = Blueprint("asimov", __name__, url_prefix="")

@bp.route("/", methods=['GET'])
def splash():
    """
    The root endpoint for asimov.

    Example
    -------

    .. http:example:: curl wget python-requests

       GET / HTTP/1.1
       Content-Type: application/json


       HTTP/1.1 200 OK
       Content-Type: application/json

       "asimov"
    """
    return make_response(jsonify(asimov.__name__), 200)

@bp.route("/version", methods=['GET'])
def version():
    """
    Show the version information for asimov and the pipelines it is designed to run.

    Example
    -------

    .. http:example:: curl wget python-requests

       GET /version HTTP/1.1
       Content-Type: application/json


       HTTP/1.1 200 OK
       Content-Type: application/json

       "v0.3.4"
    """
    return make_response(jsonify(asimov.__version__), 200)


