from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from datetime import date
from .models import Feedback, Category, Expense
from .models import SavingGoal



class ExpenseAddForm(forms.ModelForm):
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
    class Meta:
        model = Feedback
        fields = ['name', 'message', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name (optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your feedback'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

class ExpenseEditForm(forms.ModelForm):
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
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

class BudgetCycleForm(forms.Form):
    total_budget = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Monthly Budget Amount")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Start Date (optional)")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="End Date (optional)")
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")