from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Citizen

class CitizenRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    congressional_district = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = Citizen
        fields = ('username', 'email', 'password1', 'password2', 'congressional_district', 'state')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email= self.cleaned_data['email']
        user.congressional_district = self.cleaned_data['congressional_district']
        user.state = self.cleaned_data['state']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.is_premium = False
        if commit:
            user.save()
        return user