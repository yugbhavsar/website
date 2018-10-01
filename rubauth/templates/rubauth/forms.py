from django import forms

class LoginForm ( forms.Form ):
    username = forms.CharField(
        required = True
    )
    password = forms.PasswordField(
        required = True
    )
