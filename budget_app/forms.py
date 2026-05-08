from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from datetime import date
from .models import Feedback, Category, Expense
from .models import SavingGoal



class ExpenseAddForm(forms.ModelForm):
    """
    Form for creating new expenses. Includes logic for selecting existing 
    categories or dynamically adding a new category name.
    """
    # Field for existing categories
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Select a Category",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category-select'})
    )
    
    # Hidden field that only appears if "+ New Category" is picked
    new_category_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-2', 
            'placeholder': 'Enter new category name',
            'style': 'display: none;',
            'id': 'new-category-input'
        })
    )

    class Meta:
        model = Expense
        fields = ['amount', 'description', 'date']

class ExpenseFilterForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

class StyledSignUpForm(UserCreationForm):
    """
    Extended registration form with Bootstrap-styled widgets for all fields.
    Inherits validation logic from Django's built-in UserCreationForm.
    """
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']



class FeedbackForm(forms.ModelForm):
    """
    Form for collecting user feedback including an optional name,
    a message, and a numeric rating between 1 and 5.
    """
    class Meta:
        model = Feedback
        fields = ['name', 'message', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name (optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your feedback'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

class ExpenseEditForm(forms.ModelForm):
    """
    Form for modifying an existing expense record.
    Allows updating the amount, category, description, and date fields.
    """
    class Meta:
        model = Expense
        fields = ["amount", "category", "description", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class ExpenseFilterForm(forms.Form):
    """
    Form for filtering the expense history list by category and date range.
    All fields are optional to allow partial filtering.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )


class SavingGoalForm(forms.ModelForm):
    """
    Form for setting up a long-term savings target.
    Includes a custom cleaner to ensure the deadline date is set in the future.
    """
    class Meta:
        model = SavingGoal
        fields = ["title", "target_amount", "deadline"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Goal name"}),
            "target_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "deadline": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        # Validation: Deadline cannot be in the past
        if deadline and deadline < date.today():
           raise forms.ValidationError("The deadline cannot be in the past.")
        return deadline


class GoalDepositForm(forms.Form):
    """
    Form for depositing an amount toward an existing saving goal.
    Enforces a minimum deposit value of 0.01.
    """
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

class BudgetCycleForm(forms.Form):
    """
    Captures initial configuration for a budget period.
    Validates that the total budget is a positive amount and 
    manages the start and end dates of the cycle.
    """
    total_budget = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Monthly Budget Amount")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Start Date (optional)")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="End Date (optional)")
    def clean(self):
        """
        Cross-field validation to ensure the end date is strictly after the start date.

        :raises ValidationError: If end date is on or before start date.
        """
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")