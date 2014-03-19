#!/usr/bin/env python3
# -*- coding: utf-8 -*-

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'Graphite-API'
copyright = '2014, Bruno Renié'

version = '1.0'
release = '1.0'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'default'

html_static_path = ['_static']

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
