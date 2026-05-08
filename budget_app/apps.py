from django.apps import AppConfig
"""
Admin site configuration. 
Registers models to the Django Admin interface for database management and debugging.
"""

class BudgetAppConfig(AppConfig):
    """
    Configuration class for the Budget Management application.
    Handles app-ready signals and registry.
    """
    name = 'budget_app'