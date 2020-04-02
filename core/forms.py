from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from core.models import Order


class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Street 123', 'class': 'form-control'
    }))
    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100'
        })
    )
    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    you_happy = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect(), choices=Order.PAYMENT_CHOICES)


