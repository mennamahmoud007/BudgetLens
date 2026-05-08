import os
import sys
import django

sys.path.insert(0, r'C:\Users\Excellent Store\budgetlens')
os.environ['DJANGO_SETTINGS_MODULE'] = 'budgetlens.settings'
django.setup()

project = 'BudgetLens'
copyright = '2026, The 404 team'
author = 'Malak Mohamed, Menna Tullah, Shrouk Hany, Sara Hany'
release = '2026'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'alabaster'
html_static_path = ['_static']