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
    validity = forms.CharField(widget=forms.TextInput(attrs={'list':'validity_options'}))
    delivery = forms.CharField(widget=forms.TextInput(attrs={'list':'delivery_options'}))
    warranty = forms.CharField(widget=forms.TextInput(attrs={'list':'warranty_options'}), required=False)
    shipping = forms.CharField(widget=forms.TextInput(attrs={'list':'shipping_options'}), required=False)

    class Meta:
        model = Quotation
        fields = [
            'client_name','client_company','client_email','client_phone',
            'valid_until','payment_terms','salesperson','products','total_amount',
            'validity','delivery','warranty','shipping'
        ]