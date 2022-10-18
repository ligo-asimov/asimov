# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'Asimov'
copyright = '2022, Daniel Williams'
author = 'Daniel Williams'

import kentigern
import asimov
# The full version, including alpha/beta/rc tags
release = asimov.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'numpydoc',
    'sphinx_click',
    'sphinxcontrib.httpdomain',
    'sphinxcontrib.httpexample',
    'sphinxcontrib.autohttp.flask',
    'sphinx-jsonschema',
    'sphinx_multiversion'
]

html_logo = "textmark.png"
autodoc_mock_imports = ["htcondor", "git"]
templates_path = ['_templates']
language = 'en'
exclude_patterns = []
html_theme = 'kentigern'

todo_include_todos = True

# Multiversion
smv_tag_whitelist = r'^v\d+\.\d+\.?\d*$'
smv_branch_whitelist = r'^(master|review)$'
smv_released_pattern = r'^refs/tags/v\d+\.\d+\.?\d*$'
smv_latest_version = r'master'
