from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
# https://stackoverflow.com/questions/55369645/how-to-customize-default-auth-login-form-in-django/55369791
from django import forms
from django.forms.fields import CharField
from django.forms.widgets import PasswordInput


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = forms.EmailField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'hello'
        }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': '',
            'id': 'hi',
        }))


# https://stackoverflow.com/questions/35256802/how-to-implement-password-change-form-in-django-1-9
class PasswordChangeCustomForm(PasswordChangeForm):
    error_css_class = 'has-error'
    error_messages = {'password_incorrect': "请输入用户名。"}
    old_password = CharField(
        required=True,
        label='旧密码',
        widget=PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': '请输入以前的密码。'})

    new_password1 = CharField(
        required=True,
        label='新密码',
        widget=PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': '请输入新密码。'})
    new_password2 = CharField(
        required=True,
        label='新密码（确认）',
        widget=PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': '请输入新密码（确认）。'})
