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
    return make_response(jsonify(asimov.__name__), 200)

@bp.route("/version", methods=['GET'])
def version():
    return make_response(jsonify(asimov.__version__), 200)


