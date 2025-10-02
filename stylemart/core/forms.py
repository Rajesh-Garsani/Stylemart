from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Order
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")  # don't list full_name/phone here

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.username = email  # use email as username
        user.email = email
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                phone=self.cleaned_data["phone"]
            )
        return user



class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]
