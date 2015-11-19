#!/usr/bin/env python3
# coding: utf-8

import os
import re
import sys

import sphinx_rtd_theme

from sphinx.ext import autodoc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'Graphite-API'
copyright = u'2014, Bruno Renié'

version = '1.1.2'
release = '1.1.2'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

htmlhelp_basename = 'Graphite-APIdoc'

latex_elements = {
}

latex_documents = [
    ('index', 'Graphite-API.tex', 'Graphite-API Documentation',
     'Bruno Renié', 'manual'),
]

man_pages = [
    ('index', 'graphite-api', 'Graphite-API Documentation',
     ['Bruno Renié'], 1)
]

texinfo_documents = [
    ('index', 'Graphite-API', 'Graphite-API Documentation',
     'Bruno Renié', 'Graphite-API', 'One line description of project.',
     'Miscellaneous'),
]


class RenderFunctionDocumenter(autodoc.FunctionDocumenter):
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return autodoc.FunctionDocumenter.can_document_member(
            member, membername, isattr, parent
        ) and parent.name == 'graphite_api.functions'

    def format_args(self):
        args = super(RenderFunctionDocumenter, self).format_args()
        if args is not None:
            return re.sub('requestContext, ', '', args)


def setup(app):
    app.add_autodocumenter(RenderFunctionDocumenter)

add_module_names = False


class Mock(object):
    __all__ = []

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return Mock()

for mod_name in ['cairocffi']:
    sys.modules[mod_name] = Mock()
