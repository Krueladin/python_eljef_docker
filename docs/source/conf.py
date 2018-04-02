#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,redefined-builtin
"""Sphinx Configuration for ElJef Docker"""

import sys
import os

FILE_PATH = os.path.dirname(os.path.abspath(os.path.join(__file__, '../..')))
sys.path.insert(0, FILE_PATH)

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
add_module_names = False

project = 'ElJef Docker'
# noinspection PyShadowingBuiltins
copyright = '2018, Jef Oliver'
author = 'Jef Oliver'

version = '0.0.8'
release = '0.0.8'

language = None

exclude_patterns = []

pygments_style = 'sphinx'

todo_include_todos = False


html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'ElJefDockerdoc'
html_sidebars = {'**': ['indexsidebar.html', 'searchbox.html']}

latex_elements = {}
latex_documents = [
    (master_doc, 'ElJefDocker.tex', 'ElJef Docker Documentation', 'Jef Oliver', 'manual'),
]

texinfo_documents = [
    (master_doc, 'ElJefDocker', 'ElJef Docker Documentation', author, 'ElJefDocker', 'ElJef Docker functionality.',
     'Miscellaneous'),
]
