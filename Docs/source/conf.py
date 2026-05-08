import os
import sys
import django

# 1. Setup paths so Sphinx can find your code
# This points to the 'budgetlens' root directory where manage.py is located.
sys.path.insert(0, os.path.abspath('../../'))

# 2. Tell Sphinx where your Django settings are
os.environ['DJANGO_SETTINGS_MODULE'] = 'budgetlens.settings'
django.setup()

# 3. Project information
project = 'Budget Management System'
copyright = '2026, The 404 team'
author = 'Malak Mohamed Youssef  20240611 Menna Tullah Mahmoud  20242351 Shrouk Hany Sabry  20240276 Sara Hany Mostafa   20240231'

# 4. General configuration
extensions = [
    'sphinx.ext.autodoc',        # Pulls documentation from docstrings
    'sphinx.ext.viewcode',       # Adds links to your source code
    'sphinxcontrib_django',      # Essential for Django-specific documentation
]

templates_path = ['_templates']
exclude_patterns = []

# 5. Options for HTML output
# This uses the professional theme often used in software engineering.
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']