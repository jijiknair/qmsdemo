# quotes/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)  # explicitly add role

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']



class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))

from .models import Quotation

VALIDITY_CHOICES = ['7 days','10 days','15 days','30 days','3 weeks','6 months','1 year']
DELIVERY_CHOICES = ['Immediate','1 week','2 weeks','1 month']
WARRANTY_CHOICES = ['None','6 months','1 year','2 years']
SHIPPING_CHOICES = ['Standard','Express','Air','Sea']

class QuotationForm(forms.ModelForm):

    class Meta:
        model = Quotation
        fields = [
            'client',
            'intro_text',
            'closing_text',
            'terms_text',
            'valid_until',
        ]
