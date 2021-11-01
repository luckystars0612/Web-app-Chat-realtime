from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from .models import Account


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=255,help_text="Required. Add a valid email")
    class Meta:
        model = Account
        fields = ('email','username','password1','password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
        except Account.DoesNotExist:
            return email
        raise forms.ValidationError(f"Email {email} is already exist")
    def clean_username(self):
        uname = self.cleaned_data['username']
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(username=uname)
        except Account.DoesNotExist:
            return uname
        raise forms.ValidationError(f"Username {uname} is already exist")

class AccountAuthenticationForm(forms.ModelForm):
    password = forms. CharField(label="Password", widget=forms.PasswordInput)
    class Meta:
        model = Account
        fields = ("email","password")
    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email=email,password=password):
                raise forms.ValidationError("Username or password is incorrect!")

class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('username','email','profile_img','hide_email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
        except Account.DoesNotExist:
            return email
        raise forms.ValidationError(f"Email {email} is already exist")
    def clean_username(self):
        uname = self.cleaned_data['username']
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(username=uname)
        except Account.DoesNotExist:
            return uname
        raise forms.ValidationError(f"Username {uname} is already exist")
    def save(self,commit=True):
        account = super(AccountUpdateForm,self).save(commit=False)
        account.username = self.cleaned_data['username']
        account.email = self.cleaned_data['email']
        account.profile_img = self.cleaned_data['profile_img']
        account.hide_email = self.cleaned_data['hide_email']
        if commit:
            account.save()
        return account