# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'RIXA'
copyright = '2023, Finn Schwall, Fraunhofer IOSB'
author = 'Finn Schwall'
version = '0.1'
release = '0.1-alpha1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

extensions = ['sphinx.ext.autodoc', 'myst_parser', 'sphinxcontrib.mermaid']

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinxawesome_theme'
html_static_path = ['_static']

html_css_files = ["bugfix.css"]
html_theme_options = {
   "awesome_headerlinks": False,
   "main_nav_links": {
      "Home": "index",
   }
}

import os
os.environ["DOCUMENTATION_MODE"] = "True"

